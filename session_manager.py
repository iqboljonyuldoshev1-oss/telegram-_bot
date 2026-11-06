import shutil
from pathlib import Path
from config import TEMP_DIR, BASE_DIR

ROMANTIC_TRACKS = {
    "romantic_piano": "🌹 Mayin Pianino",
    "acoustic_love": "💕 Akustik Sevgi",
    "soft_romance": "✨ Sokin Romance",
    "none": "🔇 Musiqasiz"
}

class UserSession:
    def __init__(self, user_id: int):
        self.user_id = user_id
        # List of dicts: [{"type": "photo"|"video", "path": str}]
        self.media_items: list[dict] = []
        # Built-in track key: romantic_piano, acoustic_love, soft_romance, or 'none'
        self.music_choice: str = "romantic_piano"
        self.custom_audio: str | None = None
        self.style: str = "ken_burns"
        self.aspect: str = "9:16"
        self.duration: float = 3.0
        self.control_msg_id: int | None = None

        self.user_dir = TEMP_DIR / str(user_id)
        self.user_dir.mkdir(exist_ok=True)

    def add_media(self, media_type: str, file_path: str):
        self.media_items.append({"type": media_type, "path": file_path})

    def set_custom_audio(self, file_path: str):
        self.custom_audio = file_path
        self.music_choice = "custom"

    @property
    def effective_audio_path(self) -> str | None:
        if self.music_choice == "custom" and self.custom_audio and Path(self.custom_audio).exists():
            return self.custom_audio
        if self.music_choice == "none":
            return None
        built_in = BASE_DIR / "assets" / "music" / f"{self.music_choice}.mp3"
        if built_in.exists():
            return str(built_in)
        return None

    @property
    def photo_count(self) -> int:
        return sum(1 for m in self.media_items if m["type"] == "photo")

    @property
    def video_count(self) -> int:
        return sum(1 for m in self.media_items if m["type"] == "video")

    @property
    def total_count(self) -> int:
        return len(self.media_items)

    def clear(self):
        self.media_items.clear()
        self.custom_audio = None
        self.music_choice = "romantic_piano"
        self.control_msg_id = None
        if self.user_dir.exists():
            shutil.rmtree(self.user_dir, ignore_errors=True)
            self.user_dir.mkdir(exist_ok=True)


class SessionManager:
    def __init__(self):
        self._sessions: dict[int, UserSession] = {}

    def get(self, user_id: int) -> UserSession:
        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession(user_id)
        return self._sessions[user_id]

    def remove(self, user_id: int):
        if user_id in self._sessions:
            self._sessions[user_id].clear()
            del self._sessions[user_id]


session_manager = SessionManager()
