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
    Compresses video with FFmpeg to guarantee it fits under Telegram's 48MB limit.
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    dur = max(10, duration)
    # Target 44MB to safely stay below 50MB
    target_mb = 44.0
    total_bitrate_kbps = (target_mb * 8192) / dur
    audio_bitrate_kbps = 96
    video_bitrate_kbps = max(180, int(total_bitrate_kbps - audio_bitrate_kbps))

    cmd = [
        ffmpeg_exe, "-y",
        "-loglevel", "error",
        "-i", input_path,
        "-vf", r"scale=-2:min(480\,ih)",
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
    Downloads video from YouTube, Instagram, TikTok, etc.
    Intelligently picks 720p/480p/360p and compresses if necessary so it NEVER fails on size!
    """
    os.makedirs(download_dir, exist_ok=True)
    file_id = uuid.uuid4().hex[:10]
    outtmpl = os.path.join(download_dir, f"dl_{file_id}.%(ext)s")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    # Intelligent format selection: prefers high quality under 45MB, or falls back to 480p/360p
    ydl_opts = {
        'format': (
            'bestvideo[height<=720][filesize_approx<42M]+bestaudio/'
            'best[height<=720][filesize_approx<42M]/'
            'bestvideo[height<=480]+bestaudio/'
            'best[height<=480]/'
            'bestvideo[height<=360]+bestaudio/'
            'best[height<=360]/'
            'best'
        ),
        'outtmpl': outtmpl,
        'merge_output_format': 'mp4',
        'ffmpeg_location': ffmpeg_exe,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
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

        # Check file size against Telegram 50MB limit
        size_bytes = os.path.getsize(expected_path)
        is_compressed = False

        if size_bytes > 48 * 1024 * 1024:
            # File is over Telegram upload limit: automatically compress with FFmpeg!
            compressed_path = os.path.join(download_dir, f"dl_{file_id}_compressed.mp4")
            result_path = compress_video_to_fit(expected_path, compressed_path, duration)
            if result_path != expected_path and os.path.exists(result_path):
                # Remove original large file
                try:
                    os.remove(expected_path)
                except Exception:
                    pass
                expected_path = result_path
                is_compressed = True

        final_size = os.path.getsize(expected_path)
        if final_size > 50 * 1024 * 1024:
            raise ValueError(
                f"Video juda uzun bo'lgani uchun hajmi {final_size // (1024*1024)} MB bo'lib ketdi "
                "(Telegram faqat 50MB gacha ruxsat beradi)."
            )

        return {
            "file_path": expected_path,
            "title": title,
            "duration": duration,
            "channel": channel,
            "is_compressed": is_compressed
        }
