# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
import os
from pyrogram import Client, filters
from pyrogram.types import Message
import logging
from config import DOWNLOAD_DIR, MAX_FILE_SIZE
from utils import get_media_info, download_with_progress, sanitize_filename, safe_telegram_call, user_selections

logger = logging.getLogger(__name__)

def register_mediainfo_handlers(app: Client):
    @app.on_message(filters.command("mediainfo"))
    async def mediainfo_cmd(client: Client, message: Message):
        target = message.reply_to_message if message.reply_to_message else message

        if not (target.video or target.document or target.audio):
            await safe_telegram_call(message.reply, "Please reply to a video, audio, or document to get its media info.")
            return

        size = target.video.file_size if target.video else (target.document.file_size if target.document else target.audio.file_size)
        if size and size > MAX_FILE_SIZE:
            await safe_telegram_call(message.reply, f"File size exceeds {MAX_FILE_SIZE} bytes. Cannot probe.")
            return

        name = (target.video.file_name if target.video else
                (target.document.file_name if target.document else
                 (target.audio.file_name if target.audio else f"file_{target.id}")))
        if not name:
            name = f"file_{target.id}"

        path = os.path.join(DOWNLOAD_DIR, f"info_{message.from_user.id}_{sanitize_filename(name)}")

        msg = await safe_telegram_call(message.reply, "Downloading to extract media info...")

        # We use a temporary entry in user_selections for progress tracking
        chat_id, user_id = message.chat.id, message.from_user.id
        user_selections.setdefault(chat_id, {}).setdefault(user_id, {})
        user_selections[chat_id][user_id]['status_message_id'] = msg.id

        try:
            await download_with_progress(client, target, path, chat_id, user_id)
            info = await get_media_info(path)
            await safe_telegram_call(msg.edit_text, info)
        except Exception as e:
            logger.error(f"Mediainfo error: {str(e)}")
            await safe_telegram_call(msg.edit_text, f"Error: {str(e)}")
        finally:
            if os.path.exists(path):
                os.remove(path)
