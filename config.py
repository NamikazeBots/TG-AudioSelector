
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------

import os

# Telegram API credentials
API_ID = 22884130  # Replace with your API ID
API_HASH = "a69e8b16dac958f1bd31eee360ec53fa"  # Replace with your API Hash
BOT_TOKEN = "7798706143:AAHsAm7SJEswWq4szQQSgK6D5Jb-aFkxDig"  # Replace with your Bot Token

# Directory for downloads
DOWNLOAD_DIR = "downloads"

# Allowed group IDs
ALLOWED_GROUP_IDS = [
    -1001234567890,  # Your group ID from logs (example ID)
    # Add more group IDs as needed
]

# Owner user ID
OWNER_ID = 7840980054  # Owner's user ID

# Maximum file size (e.g., 4GB)
MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB in bytes

# Premium users and daily limits
PREMIUM_USERS = {5756495153}  # Add premium user IDs here
DAILY_LIMIT_FREE = 15  # Videos per day for free users
DAILY_LIMIT_PREMIUM = 30  # Videos per day for premium users

# MongoDB Configuration
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "audio_selector_bot")

# Database Channel for forwarding files
DB_CHANNEL_ID = int(os.environ.get("DB_CHANNEL_ID", -1001234567890))

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
if not os.access(DOWNLOAD_DIR, os.W_OK):
    raise PermissionError(f"No write permission for {DOWNLOAD_DIR}")
