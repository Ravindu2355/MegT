import os
#from dotenv import load_dotenv
#load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
USE_USERBOT = os.getenv("USE_USERBOT", "false").lower() in ("1","true","yes")
SESSION_STRING = os.getenv("SESSION_STRING", "")
WORK_DIR = os.getenv("WORK_DIR", "/tmp/mega_bot")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(2147483648)))  # default 2GB
POST_UPLOAD_WAIT = int(os.getenv("POST_UPLOAD_WAIT", "30"))
MEGA_CLI = os.getenv("MEGA_CLI", "megadl")  # use megadl (megatools) or mega-get (megacmd)
os.makedirs(WORK_DIR, exist_ok=True)
INDEX_FILE = os.path.join(WORK_DIR, "mega_index.json")
DOWNLOADS_DIR = os.path.join(WORK_DIR, "downloads")
THUMB_DIR = os.path.join(WORK_DIR, "thumbs")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)
