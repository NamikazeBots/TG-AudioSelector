
from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID
from database import db

@Client.on_message(filters.command("auth") & filters.user(OWNER_ID))
async def auth_chat(client: Client, message: Message):
    chat_id = message.chat.id
    if db: await db.add_auth(chat_id)
    await message.reply(f"Chat {chat_id} authorized.")

@Client.on_message(filters.command("unauth") & filters.user(OWNER_ID))
async def unauth_chat(client: Client, message: Message):
    chat_id = message.chat.id
    if db: await db.remove_auth(chat_id)
    await message.reply(f"Chat {chat_id} unauthorized.")
