
import motor.motor_asyncio
from config import MONGO_URI, DATABASE_NAME
from datetime import datetime

class Database:
    def __init__(self):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        self._db = self._client[DATABASE_NAME]
        self._auth = self._db["authorized"]
        self._users = self._db["users"]
        self._limits = self._db["daily_limits"]

    async def add_authorized_id(self, chat_id: int):
        await self._auth.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id, "authorized_at": datetime.now()}},
            upsert=True
        )

    async def remove_authorized_id(self, chat_id: int):
        await self._auth.delete_one({"chat_id": chat_id})

    async def is_authorized(self, chat_id: int):
        res = await self._auth.find_one({"chat_id": chat_id})
        return res is not None

    async def save_user_settings(self, user_id: int, settings: dict):
        await self._users.update_one(
            {"user_id": user_id},
            {"$set": settings},
            upsert=True
        )

    async def get_user_settings(self, user_id: int):
        res = await self._users.find_one({"user_id": user_id})
        return res or {}

    async def get_daily_limit(self, user_id: int):
        res = await self._limits.find_one({"user_id": user_id})
        if not res:
            return {'count': 0, 'last_reset': datetime.now()}
        return res

    async def update_daily_limit(self, user_id: int, count: int, last_reset: datetime):
        await self._limits.update_one(
            {"user_id": user_id},
            {"$set": {"count": count, "last_reset": last_reset}},
            upsert=True
        )

db = Database()
