
import motor.motor_asyncio
from config import MONGO_DB_URL, ALLOWED_GROUP_IDS
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.auth_chats = self.db.auth_chats
        self.users = self.db.users
        self.daily_limits = self.db.daily_limits

    async def add_auth(self, chat_id):
        await self.auth_chats.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id, "authorized": True}},
            upsert=True
        )

    async def remove_auth(self, chat_id):
        await self.auth_chats.delete_one({"chat_id": chat_id})

    async def is_auth(self, chat_id):
        if chat_id in ALLOWED_GROUP_IDS:
            return True
        chat = await self.auth_chats.find_one({"chat_id": chat_id})
        return chat is not None

    async def set_user_setting(self, user_id, key, value):
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {key: value}},
            upsert=True
        )

    async def get_user_setting(self, user_id, key, default=None):
        user = await self.users.find_one({"user_id": user_id})
        if user:
            return user.get(key, default)
        return default

    async def get_all_user_settings(self, user_id):
        return await self.users.find_one({"user_id": user_id}) or {}

    async def increment_daily_count(self, user_id):
        today = datetime.now().strftime("%Y-%m-%d")
        await self.daily_limits.update_one(
            {"user_id": user_id, "date": today},
            {"$inc": {"count": 1}},
            upsert=True
        )

    async def get_daily_count(self, user_id):
        today = datetime.now().strftime("%Y-%m-%d")
        data = await self.daily_limits.find_one({"user_id": user_id, "date": today})
        if data:
            return data.get("count", 0)
        return 0

db = None
if MONGO_DB_URL:
    db = Database(MONGO_DB_URL, "audio_selector_bot")
else:
    logger.warning("MONGO_DB_URL not set. Database features will be disabled or limited.")
