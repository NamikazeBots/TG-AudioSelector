
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API credentials
API_ID = int(os.environ.get("API_ID", 22884130))
API_HASH = os.environ.get("API_HASH", "a69e8b16dac958f1bd31eee360ec53fa")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8461268419:AAECYUlcecWsMkemTu1fW-Id2f-5A8AHT-0")

# MongoDB URL
MONGO_DB_URL = os.environ.get("MONGO_DB_URL", "mongodb+srv://Fugui:tianlu@cluster0.6hyrp0r.mongodb.net/?appName=Cluster0")

# DB Channel ID
DB_CHANNEL_ID = int(os.environ.get("DB_CHANNEL_ID", "-1003215117714"))

# Directory for downloads
DOWNLOAD_DIR = "downloads"

# Allowed group IDs
ALLOWED_GROUP_IDS = [
    -1001234567890,  # Your group ID from logs (example ID)
    # Add more group IDs as needed
]

# Owner user ID
OWNER_ID = int(os.environ.get("OWNER_ID", 8497538010))

# Maximum file size (e.g., 4GB)
MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB in bytes

# Premium users and daily limits
PREMIUM_USERS = set()  # Add premium user IDs here
DAILY_LIMIT_FREE = 15  # Videos per day for free users
DAILY_LIMIT_PREMIUM = 30  # Videos per day for premium users

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
if not os.access(DOWNLOAD_DIR, os.W_OK):
    raise PermissionError(f"No write permission for {DOWNLOAD_DIR}")
