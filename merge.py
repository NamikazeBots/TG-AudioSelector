# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType
import logging
from config import DOWNLOAD_DIR, MAX_FILE_SIZE, ALLOWED_GROUP_IDS, OWNER_ID
from utils import (
    download_with_progress, sanitize_filename, safe_telegram_call,
    user_selections, merge_files, merge_files_ffmpeg, upload_with_progress,
    generate_thumbnail
)

logger = logging.getLogger(__name__)

def register_merge_handlers(app: Client):
    async def is_merging_filter(_, __, message: Message):
        chat_id, user_id = message.chat.id, message.from_user.id
        return user_id in merge_files.get(chat_id, {})

    merging = filters.create(is_merging_filter)

    @app.on_message(filters.command("merge"))
    async def merge_cmd(client: Client, message: Message):
        chat_id, user_id = message.chat.id, message.from_user.id

        if user_id != OWNER_ID and chat_id not in ALLOWED_GROUP_IDS:
            await safe_telegram_call(message.reply, "This bot is not authorized here.")
            return

        merge_files[chat_id][user_id] = []
        await safe_telegram_call(message.reply, "Merge mode activated. Send the files you want to merge (video, audio, or subtitles) one by one.\n\n"
                                "If you send multiple videos, they will be joined together.\n"
                                "If you send one video and others are audio/subtitles, they will be muxed.\n\n"
                                "When finished, click 'Merge Now'.",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("Merge Now", callback_data="merge_now")],
                                    [InlineKeyboardButton("Cancel", callback_data="merge_cancel")]
                                ]))

    @app.on_message((filters.video | filters.document | filters.audio) & merging)
    async def collect_merge_files(client: Client, message: Message):
        chat_id, user_id = message.chat.id, message.from_user.id

        size = (message.video.file_size if message.video else
                (message.document.file_size if message.document else message.audio.file_size))
        if size and size > MAX_FILE_SIZE:
            await safe_telegram_call(message.reply, f"File too large. Maximum allowed size is {MAX_FILE_SIZE} bytes.")
            return

        name = (message.video.file_name if message.video else
                (message.document.file_name if message.document else (message.audio.file_name if message.audio else f"merge_{message.id}")))
        if not name:
            name = f"merge_{message.id}"

        path = os.path.join(DOWNLOAD_DIR, f"merge_{user_id}_{sanitize_filename(name)}")

        msg = await safe_telegram_call(message.reply, f"Downloading file {len(merge_files[chat_id][user_id]) + 1} for merge...")

        user_selections.setdefault(chat_id, {}).setdefault(user_id, {})
        user_selections[chat_id][user_id]['status_message_id'] = msg.id

        try:
            await download_with_progress(client, message, path, chat_id, user_id)
            merge_files[chat_id][user_id].append(path)
            await safe_telegram_call(msg.edit_text, f"File {len(merge_files[chat_id][user_id])} downloaded. Send more files or click 'Merge Now'.",
                                    reply_markup=InlineKeyboardMarkup([
                                        [InlineKeyboardButton("Merge Now", callback_data="merge_now")],
                                        [InlineKeyboardButton("Cancel", callback_data="merge_cancel")]
                                    ]))
        except Exception as e:
            logger.error(f"Download error in merge: {str(e)}")
            await safe_telegram_call(msg.edit_text, f"Error: {str(e)}")

    @app.on_callback_query(filters.regex("^merge_"))
    async def merge_callback(client: Client, cq):
        chat_id, user_id = cq.message.chat.id, cq.from_user.id
        data = cq.data

        if data == "merge_cancel":
            for f in merge_files.get(chat_id, {}).get(user_id, []):
                if os.path.exists(f): os.remove(f)
            del merge_files[chat_id][user_id]
            await safe_telegram_call(cq.message.edit_text, "Merge process cancelled.")
            return

        if data == "merge_now":
            files = merge_files.get(chat_id, {}).get(user_id, [])
            if len(files) < 2:
                await cq.answer("Please send at least two files to merge.", show_alert=True)
                return

            await safe_telegram_call(cq.message.edit_text, "Merging files... please wait.")

            outname = f"merged_{user_id}_{sanitize_filename(os.path.basename(files[0]))}"
            dst = os.path.join(DOWNLOAD_DIR, os.path.splitext(outname)[0] + ".mkv")
            thumb = os.path.join(DOWNLOAD_DIR, f"{os.path.splitext(outname)[0]}.jpg")

            try:
                await merge_files_ffmpeg(files, dst)
                await generate_thumbnail(dst, thumb)

                await safe_telegram_call(cq.message.edit_text, "Uploading merged file...")
                await upload_with_progress(client, chat_id, user_id, dst, "Merged by Bot", "mkv", thumb)

                await safe_telegram_call(cq.message.edit_text, "Merge completed successfully!")
            except Exception as e:
                logger.error(f"Merge error: {str(e)}")
                await safe_telegram_call(cq.message.edit_text, f"Error during merge: {str(e)}")
            finally:
                for f in files:
                    if os.path.exists(f): os.remove(f)
                if os.path.exists(dst): os.remove(dst)
                if os.path.exists(thumb): os.remove(thumb)
                if user_id in merge_files.get(chat_id, {}):
                    del merge_files[chat_id][user_id]
