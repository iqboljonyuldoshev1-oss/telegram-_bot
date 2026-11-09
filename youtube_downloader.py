import os
import re
import uuid
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

def download_video_link(url: str, download_dir: str) -> dict:
    """
    Downloads video from YouTube, Instagram, TikTok, etc. using yt-dlp.
    Optimized for Telegram Bot API limits (under 50MB).
    """
    os.makedirs(download_dir, exist_ok=True)
    file_id = uuid.uuid4().hex[:10]
    outtmpl = os.path.join(download_dir, f"dl_{file_id}.%(ext)s")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    ydl_opts = {
        'format': (
            'bestvideo[ext=mp4][height<=1080][filesize<?45M]+bestaudio[ext=m4a]/'
            'bestvideo[height<=720][filesize<?45M]+bestaudio/'
            'best[filesize<?48M]/'
            'best[height<=720]/'
            'best'
        ),
        'outtmpl': outtmpl,
        'merge_output_format': 'mp4',
        'ffmpeg_location': ffmpeg_exe,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'max_filesize': 49 * 1024 * 1024,
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

        # Find the resulting file
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
        if size_bytes > 50 * 1024 * 1024:
            raise ValueError("Video hajmi 50 MB dan katta (Telegram bot limiti 50MB).")

        return {
            "file_path": expected_path,
            "title": title,
            "duration": duration,
            "channel": channel
        }
