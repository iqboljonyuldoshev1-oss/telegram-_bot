import os
import re
import uuid
import subprocess
import yt_dlp
import imageio_ffmpeg

URL_PATTERN = re.compile(
    r'(https?://[^\s]+|(?:www\.)?(?:youtube\.com|youtu\.be|instagram\.com|tiktok\.com|pin\.it)[^\s]+)',
    re.IGNORECASE
)

# Max limit requested: 100 MB
MAX_ALLOWED_SIZE_BYTES = 100 * 1024 * 1024

def is_downloadable_url(text: str) -> bool:
    if not text:
        return False
    return bool(URL_PATTERN.search(text))

def extract_url(text: str) -> str | None:
    match = URL_PATTERN.search(text)
    if not match:
        return None
    url = match.group(0).strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url

def compress_video_to_fit(input_path: str, output_path: str, duration: int) -> str:
    """
    Compresses videos up to 100MB so they fit Telegram's delivery buffer (~46-48MB).
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    dur = max(10, duration)
    target_mb = 45.0
    total_bitrate_kbps = (target_mb * 8192) / dur
    audio_bitrate_kbps = 96 if dur < 900 else 64
    video_bitrate_kbps = max(140, int(total_bitrate_kbps - audio_bitrate_kbps))

    scale_filter = r"scale=-2:min(720\,ih)" if dur < 300 else r"scale=-2:min(480\,ih)"

    cmd = [
        ffmpeg_exe, "-y",
        "-loglevel", "error",
        "-i", input_path,
        "-vf", scale_filter,
        "-c:v", "libx264",
        "-b:v", f"{video_bitrate_kbps}k",
        "-maxrate", f"{int(video_bitrate_kbps * 1.3)}k",
        "-bufsize", f"{int(video_bitrate_kbps * 2)}k",
        "-preset", "faster",
        "-c:a", "aac",
        "-b:a", f"{audio_bitrate_kbps}k",
        output_path
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(output_path) and os.path.getsize(output_path) <= 49 * 1024 * 1024:
        return output_path
    return input_path

def download_video_link(url: str, download_dir: str) -> dict:
    """
    Downloads video from YouTube, Instagram, TikTok up to 100MB.
    Automatically compresses files between 48MB-100MB so Telegram can deliver them!
    """
    os.makedirs(download_dir, exist_ok=True)
    file_id = uuid.uuid4().hex[:10]
    outtmpl = os.path.join(download_dir, f"dl_{file_id}.%(ext)s")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    # Formats targeting up to 100MB (1080p, 720p, 480p)
    ydl_opts = {
        'format': (
            'bestvideo[height<=1080][filesize_approx<95M]+bestaudio/'
            'best[height<=1080][filesize_approx<95M]/'
            'bestvideo[height<=720][filesize_approx<95M]+bestaudio/'
            'best[height<=720]/'
            'bestvideo[height<=480]+bestaudio/'
            'best[height<=480]/'
            'best'
        ),
        'outtmpl': outtmpl,
        'merge_output_format': 'mp4',
        'ffmpeg_location': ffmpeg_exe,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'max_filesize': MAX_ALLOWED_SIZE_BYTES, # 100 MB
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web']
            }
        },
        'http_headers': {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            )
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'Video')
        duration = info.get('duration', 0)
        channel = info.get('uploader') or info.get('channel') or info.get('creator', 'Yuklandi')

        # Find the downloaded file
        expected_path = os.path.join(download_dir, f"dl_{file_id}.mp4")
        if not os.path.exists(expected_path):
            for f in os.listdir(download_dir):
                if f.startswith(f"dl_{file_id}"):
                    expected_path = os.path.join(download_dir, f)
                    break

        if not os.path.exists(expected_path):
            raise FileNotFoundError("Video yuklab olindi, lekin fayl topilmadi.")

        orig_size = os.path.getsize(expected_path)
        is_compressed = False

        # If file is larger than Telegram bot upload limit (48MB), compress it!
        if orig_size > 48 * 1024 * 1024:
            compressed_path = os.path.join(download_dir, f"dl_{file_id}_compressed.mp4")
            result_path = compress_video_to_fit(expected_path, compressed_path, duration)
            if result_path != expected_path and os.path.exists(result_path):
                try:
                    os.remove(expected_path)
                except Exception:
                    pass
                expected_path = result_path
                is_compressed = True

        final_size = os.path.getsize(expected_path)
        if final_size > 50 * 1024 * 1024:
            raise ValueError(
                f"Video hajmi 100 MB dan ham katta ({orig_size // (1024*1024)} MB). "
                "Iltimos, 100 MB gacha bo'lgan videolarni yuboring."
            )

        return {
            "file_path": expected_path,
            "title": title,
            "duration": duration,
            "channel": channel,
            "orig_size_mb": round(orig_size / (1024 * 1024), 1),
            "is_compressed": is_compressed
        }
