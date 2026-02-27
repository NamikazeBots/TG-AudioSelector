
from pyrogram import Client, filters
from pyrogram.types import Message
from database import db
from utils import authorized_only, user_selections, sanitize_filename

@Client.on_message(filters.command("us"))
@authorized_only
async def set_user_settings(client: Client, message: Message):
    user_id = message.from_user.id
    args = message.command[1:]
    if not args:
        settings = await db.get_all_user_settings(user_id) if db else user_selections.get(message.chat.id, {}).get(user_id, {})
        if not isinstance(settings, dict): settings = {}
        await message.reply(f"Settings:\nName: {settings.get('default_name', 'Not set')}\nCaption: {settings.get('default_caption', 'Not set')}")
        return
    if len(args) < 2:
        await message.reply("Usage: /us <name> <caption>")
        return
    name, caption = sanitize_filename(args[0]), args[1]
    if db:
        await db.set_user_setting(user_id, 'default_name', name)
        await db.set_user_setting(user_id, 'default_caption', caption)
    else:
        user_selections.setdefault(message.chat.id, {}).setdefault(user_id, {})['default_name'] = name
        user_selections[message.chat.id][user_id]['default_caption'] = caption
    await message.reply("Settings updated.")
