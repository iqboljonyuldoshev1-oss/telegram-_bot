import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Directory for user uploaded media and rendered videos
TEMP_DIR = BASE_DIR / "temp_media"
TEMP_DIR.mkdir(exist_ok=True)

