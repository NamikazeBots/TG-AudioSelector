
from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID
from database import db
from utils import safe_telegram_call
import logging

logger = logging.getLogger(__name__)

def register_auth_handlers(app: Client):
    @app.on_message(filters.command("auth") & filters.user(OWNER_ID))
    async def auth_chat(client: Client, message: Message):
        chat_id = message.chat.id
        if len(message.command) > 1:
            try:
                chat_id = int(message.command[1])
            except ValueError:
                await safe_telegram_call(message.reply, "Invalid Chat ID.")
                return

        if not db:
            await safe_telegram_call(message.reply, "Database not connected.")
            return

        await db.add_auth(chat_id)
        await safe_telegram_call(message.reply, f"Chat {chat_id} has been authorized.")

    @app.on_message(filters.command("unauth") & filters.user(OWNER_ID))
    async def unauth_chat(client: Client, message: Message):
        chat_id = message.chat.id
        if len(message.command) > 1:
            try:
                chat_id = int(message.command[1])
            except ValueError:
                await safe_telegram_call(message.reply, "Invalid Chat ID.")
                return

        if not db:
            await safe_telegram_call(message.reply, "Database not connected.")
            return

        await db.remove_auth(chat_id)
        await safe_telegram_call(message.reply, f"Chat {chat_id} has been deauthorized.")
