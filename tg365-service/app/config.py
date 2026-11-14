import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
IG_APP_ID = os.environ.get("IG_APP_ID", "")
IG_APP_SECRET = os.environ.get("IG_APP_SECRET", "")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
PORT = int(os.environ.get("PORT", "8000"))
EMBEDDED = os.environ.get("EMBEDDED", "0") == "1"

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))
AUDIOS_DIR = os.path.join(DATA_DIR, "audios")
WORK_DIR = os.path.join(DATA_DIR, "work")
PUBLISHED_DIR = os.path.join(DATA_DIR, "published")
DB_PATH = os.environ.get("DB_PATH", os.path.join(DATA_DIR, "bot.db"))

BRAND_NAME = "THE365NEWS"
BRAND_HANDLE = "@THE365NEWS"
OUTRO_TEXT = "با ما از مهمترین<br>اخبار روز مطلع شوید"

for _d in (DATA_DIR, AUDIOS_DIR, WORK_DIR, PUBLISHED_DIR):
    os.makedirs(_d, exist_ok=True)
