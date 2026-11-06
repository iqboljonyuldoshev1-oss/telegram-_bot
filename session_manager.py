import shutil
from pathlib import Path
from config import TEMP_DIR

class UserSession:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.photos: list[str] = []
        self.audio: str | None = None
        self.style: str = "ken_burns"
        self.aspect: str = "9:16"
        self.duration: float = 2.5
        self.control_msg_id: int | None = None

        self.user_dir = TEMP_DIR / str(user_id)
        self.user_dir.mkdir(exist_ok=True)

    def add_photo(self, file_path: str):
        self.photos.append(file_path)

    def set_audio(self, file_path: str):
        self.audio = file_path

    def clear(self):
        self.photos.clear()
        self.audio = None
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

