# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------

import os
import zipfile
import shutil
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatType
import logging
from config import DOWNLOAD_DIR, OWNER_ID, MAX_FILE_SIZE, PREMIUM_USERS, DAILY_LIMIT_FREE, DAILY_LIMIT_PREMIUM
from database import db
from utils import (
    get_audio_tracks, select_audio_tracks, download_with_progress,
    upload_with_progress, create_track_selection_keyboard,
    create_format_selection_keyboard, user_selections, sanitize_filename,
    validate_video_file, generate_thumbnail, check_daily_limit, safe_telegram_call,
    authorized_only
)
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
logger = logging.getLogger(__name__)
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
def register_video_handlers(app: Client):
    @app.on_message(filters=filters.video | filters.document)
    @authorized_only
    async def handle_message(client: Client, message: Message):
        chat_id, user_id = message.chat.id, message.from_user.id

        if user_id != OWNER_ID and message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await safe_telegram_call(message.reply, "This bot works only in groups.")
            return
        if not await check_daily_limit(user_id):
            limit = DAILY_LIMIT_PREMIUM if user_id in PREMIUM_USERS else DAILY_LIMIT_FREE
            await safe_telegram_call(message.reply, f"Daily limit of {limit} videos reached.")
            return
        if user_selections.get(chat_id, {}).get(user_id, {}).get('processing'):
            user_selections[chat_id][user_id]['queue'].append(message)
            pos = len(user_selections[chat_id][user_id]['queue'])
            await safe_telegram_call(message.reply, f"You already have a process. Queue position: {pos}")
            return
        if not message.video and not message.document:
            await safe_telegram_call(message.reply, "Please send a video file.")
            return
        size = message.video.file_size if message.video else message.document.file_size
        if size and size > MAX_FILE_SIZE:
            await safe_telegram_call(message.reply, f"File size exceeds {MAX_FILE_SIZE} bytes")
            return
        name = message.video.file_name if message.video else message.document.file_name
        if not name:
            name = f"video_{message.id}.mp4"
        # Load user settings from DB
        if db:
            user_settings = await db.get_all_user_settings(user_id)
            if 'default_name' in user_settings:
                name = user_settings['default_name']
            if 'default_caption' in user_settings:
                user_selections.setdefault(chat_id, {}).setdefault(user_id, {})['default_caption'] = user_settings['default_caption']

        path = os.path.join(DOWNLOAD_DIR, f"{user_id}_{sanitize_filename(name)}")
        user_selections.setdefault(chat_id, {}).setdefault(user_id, {'processing': True, 'queue': [], 'original_message_id': message.id})
        user_selections[chat_id][user_id]['status'] = "Starting download..."
        msg = await safe_telegram_call(message.reply, "Starting download...")
        user_selections[chat_id][user_id]['status_message_id'] = msg.id
        await download_with_progress(client, message, path, chat_id, user_id)

        # Zip file support
        if name.lower().endswith(".zip"):
            user_selections[chat_id][user_id]['status'] = "Extracting zip..."
            await safe_telegram_call(client.edit_message_text, chat_id, msg.id, "Extracting zip...")
            extract_dir = os.path.join(DOWNLOAD_DIR, f"extract_{user_id}_{message.id}")
            os.makedirs(extract_dir, exist_ok=True)
            try:
                with zipfile.ZipFile(path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                os.remove(path) # Remove zip file

                # Find the first video file
                video_file = None
                for root, dirs, files in os.walk(extract_dir):
                    for f in files:
                        f_path = os.path.join(root, f)
                        if validate_video_file(f_path):
                            video_file = f_path
                            break
                    if video_file: break

                if not video_file:
                    shutil.rmtree(extract_dir)
                    await safe_telegram_call(client.edit_message_text, chat_id, msg.id, "No valid video file found in zip.")
                    user_selections[chat_id][user_id]['processing'] = False
                    return

                # Move video file to DOWNLOAD_DIR and update path
                new_path = os.path.join(DOWNLOAD_DIR, f"{user_id}_{sanitize_filename(os.path.basename(video_file))}")
                os.rename(video_file, new_path)
                path = new_path
                shutil.rmtree(extract_dir)
            except Exception as e:
                logger.error(f"Zip extraction failed: {str(e)}")
                if os.path.exists(extract_dir): shutil.rmtree(extract_dir)
                await safe_telegram_call(client.edit_message_text, chat_id, msg.id, f"Zip extraction failed: {str(e)}")
                user_selections[chat_id][user_id]['processing'] = False
                return

        if not validate_video_file(path):
            if os.path.exists(path): os.remove(path)
            await safe_telegram_call(client.edit_message_text, chat_id, msg.id, "Invalid video file.")
            user_selections[chat_id][user_id]['processing'] = False
            return
        tracks = get_audio_tracks(path)
        if not tracks:
            os.remove(path)
            await safe_telegram_call(client.edit_message_text, chat_id, msg.id, "No audio tracks found.")
            user_selections[chat_id][user_id]['processing'] = False
            return
        user_selections[chat_id][user_id].update({'file_path': path, 'selected_tracks': set(), 'output_format': None, 'status': 'Selecting tracks...', 'last_percent': 0})
        await safe_telegram_call(client.edit_message_text, chat_id, msg.id, "Select tracks:", reply_markup=await create_track_selection_keyboard(chat_id, user_id, tracks))
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
    @app.on_callback_query()
    async def handle_callback(client: Client, cq):
        chat_id, user_id = cq.message.chat.id, cq.from_user.id
        if user_id not in user_selections.get(chat_id, {}):
            await cq.answer("This is not your session.", show_alert=True)
            return
        data = cq.data
        status_message_id = user_selections[chat_id][user_id].get('status_message_id')
        if data.startswith("track_"):
            idx = int(data.split("_")[1])
            st = user_selections[chat_id][user_id]['selected_tracks']
            st.remove(idx) if idx in st else st.add(idx)
            tracks = get_audio_tracks(user_selections[chat_id][user_id]['file_path'])
            user_selections[chat_id][user_id]['status'] = "Selecting tracks..."
            await safe_telegram_call(
                client.edit_message_text,
                chat_id,
                status_message_id,
                "Select tracks:",
                reply_markup=await create_track_selection_keyboard(chat_id, user_id, tracks)
            )
        elif data == "done_tracks":
            if not user_selections[chat_id][user_id]['selected_tracks']:
                await safe_telegram_call(cq.message.reply, "Select at least one track.")
                return
            user_selections[chat_id][user_id]['status'] = "Selecting output format..."
            await safe_telegram_call(
                client.edit_message_text,
                chat_id,
                status_message_id,
                "Select output format:",
                reply_markup=await create_format_selection_keyboard()
            )
        elif data.startswith("format_"):
            fmt = data.split("_")[1]
            info = user_selections[chat_id][user_id]
            info['output_format'] = fmt
            src = info['file_path']
            outname = info.get('default_name') or f"processed_{user_id}_{os.path.basename(src)}"
            dst = os.path.join(DOWNLOAD_DIR, sanitize_filename(outname))
            if fmt == "mkv": dst = os.path.splitext(dst)[0] + ".mkv"
            thumb = os.path.join(DOWNLOAD_DIR, f"{os.path.splitext(outname)[0]}.jpg")
            info['status'] = "Processing video..."
            await safe_telegram_call(client.edit_message_text, chat_id, status_message_id, "Processing video...")
            select_audio_tracks(src, dst, list(info['selected_tracks']), fmt)
            generate_thumbnail(src, thumb)

            # Use default caption from DB if available
            cap = info.get('default_caption')
            if not cap and db:
                cap = await db.get_user_setting(user_id, 'default_caption')
            if not cap:
                cap = "Here is your video."

            info['status'] = "Uploading video..."
            await safe_telegram_call(client.edit_message_text, chat_id, status_message_id, "Uploading video...")
            await upload_with_progress(client, chat_id, user_id, dst, cap, fmt, thumb, reply_to_message_id=info.get('original_message_id'))
            for f in [src, dst, thumb]:
                if os.path.exists(f): os.remove(f)
            user_selections[chat_id][user_id]['processing'] = False
            del user_selections[chat_id][user_id]['file_path']
            info['status'] = "Completed"
            await safe_telegram_call(client.edit_message_text, chat_id, status_message_id, "Completed")
            await safe_telegram_call(cq.message.delete)
            if user_selections[chat_id][user_id]['queue']:
                nxt = user_selections[chat_id][user_id]['queue'].pop(0)



# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------                