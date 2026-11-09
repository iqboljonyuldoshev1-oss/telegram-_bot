import os
import re
import uuid
from pathlib import Path
import yt_dlp
import imageio_ffmpeg

YOUTUBE_REGEX = re.compile(
    r'(https?://)?(www\.|m\.)?(youtube\.com/(watch\?v=|shorts/|embed/|v/)|youtu\.be/)([\w\-]+)'
)

def is_youtube_url(text: str) -> bool:
    if not text:
        return False
    return bool(YOUTUBE_REGEX.search(text))

def extract_youtube_url(text: str) -> str | None:
    match = YOUTUBE_REGEX.search(text)
    if match:
        return match.group(0)
    return None

def download_youtube_video(url: str, download_dir: str) -> dict:
    """
    Downloads YouTube video or short, returns metadata and file path.
    Uses imageio-ffmpeg as ffmpeg backend for muxing.
    Prefers mp4 format under 50MB for Telegram direct upload limit.
    """
    os.makedirs(download_dir, exist_ok=True)
    file_id = uuid.uuid4().hex[:10]
    outtmpl = os.path.join(download_dir, f"yt_{file_id}.%(ext)s")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    ydl_opts = {
        'format': (
            'bestvideo[ext=mp4][height<=1080][filesize<?45M]+bestaudio[ext=m4a]/'
            'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/'
            'best[ext=mp4][filesize<?48M]/'
            'best[ext=mp4]/'
            'best'
        ),
        'outtmpl': outtmpl,
        'merge_output_format': 'mp4',
        'ffmpeg_location': ffmpeg_exe,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'max_filesize': 49 * 1024 * 1024, # 49MB max for Telegram Bot API limit
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Find the downloaded file
        title = info.get('title', 'YouTube Video')
        duration = info.get('duration', 0)
        channel = info.get('uploader') or info.get('channel', 'YouTube')
        thumbnail = info.get('thumbnail')

        # Locate output file
        expected_path = os.path.join(download_dir, f"yt_{file_id}.mp4")
        if not os.path.exists(expected_path):
            # Scan for file starting with yt_{file_id}
            for f in os.listdir(download_dir):
                if f.startswith(f"yt_{file_id}"):
                    expected_path = os.path.join(download_dir, f)
                    break

        if not os.path.exists(expected_path):
            raise FileNotFoundError("Video yuklab olindi, lekin fayl topilmadi.")

        return {
            "file_path": expected_path,
            "title": title,
            "duration": duration,
            "channel": channel,
            "thumbnail": thumbnail
        }

