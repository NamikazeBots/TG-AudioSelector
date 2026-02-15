
from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID
from database import db
from utils import safe_telegram_call
import logging

logger = logging.getLogger(__name__)

def register_auth_handlers(app: Client):
    @app.on_message(filters.command("auth") & filters.user(OWNER_ID))
    async def auth_command(client: Client, message: Message):
        args = message.text.split()
        if len(args) < 2:
            target_id = message.chat.id
        else:
            try:
                target_id = int(args[1])
            except ValueError:
                await safe_telegram_call(message.reply, "Invalid ID format.")
                return

        await db.add_authorized_id(target_id)
        await safe_telegram_call(message.reply, f"Authorized ID: {target_id}")

    @app.on_message(filters.command("unauth") & filters.user(OWNER_ID))
    async def unauth_command(client: Client, message: Message):
        args = message.text.split()
        if len(args) < 2:
            target_id = message.chat.id
        else:
            try:
                target_id = int(args[1])
            except ValueError:
                await safe_telegram_call(message.reply, "Invalid ID format.")
                return

        await db.remove_authorized_id(target_id)
        await safe_telegram_call(message.reply, f"Unauthorized ID: {target_id}")
