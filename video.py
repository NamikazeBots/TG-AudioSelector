# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------

import os
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatType
import logging
from config import DOWNLOAD_DIR, ALLOWED_GROUP_IDS, OWNER_ID, MAX_FILE_SIZE, PREMIUM_USERS, DAILY_LIMIT_FREE, DAILY_LIMIT_PREMIUM
from utils import (
    get_audio_tracks, get_subtitle_tracks, process_video, download_with_progress,
    upload_with_progress, create_track_selection_keyboard, create_subtitle_selection_keyboard,
    create_format_selection_keyboard, create_resolution_selection_keyboard,
    user_selections, sanitize_filename, validate_video_file, generate_thumbnail,
    check_daily_limit, safe_telegram_call
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
async def process_next_in_queue(client: Client, chat_id: int, user_id: int):
    if user_selections.get(chat_id, {}).get(user_id, {}).get('queue'):
        nxt = user_selections[chat_id][user_id]['queue'].pop(0)
        # We need to call the handler for the next message
        await handle_video_message(client, nxt)

async def handle_video_message(client: Client, message: Message):
    chat_id, user_id = message.chat.id, message.from_user.id

    # Check if user is in merge mode
    from utils import merge_files
    if user_id in merge_files.get(chat_id, {}):
        return

    if user_id != OWNER_ID and chat_id not in ALLOWED_GROUP_IDS:
        logger.info(f"Unauthorized access attempt: user_id={user_id}, chat_id={chat_id}, allowed_ids={ALLOWED_GROUP_IDS}")
        await safe_telegram_call(message.reply, "This bot is not authorized here.")
        return
    if user_id != OWNER_ID and message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await safe_telegram_call(message.reply, "This bot works only in groups.")
        return
    if not check_daily_limit(user_id):
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
    if user_id in user_selections.get(chat_id, {}) and 'default_name' in user_selections[chat_id][user_id]:
        name = user_selections[chat_id][user_id]['default_name']
    path = os.path.join(DOWNLOAD_DIR, f"{user_id}_{sanitize_filename(name)}")
    user_selections.setdefault(chat_id, {}).setdefault(user_id, {'processing': True, 'queue': [], 'original_message_id': message.id})
    user_selections[chat_id][user_id]['status'] = "Starting download..."
    msg = await safe_telegram_call(message.reply, "Starting download...")
    user_selections[chat_id][user_id]['status_message_id'] = msg.id
    try:
        await download_with_progress(client, message, path, chat_id, user_id)
        if not await validate_video_file(path):
            os.remove(path)
            await safe_telegram_call(client.edit_message_text, chat_id, msg.id, "Invalid video file.")
            user_selections[chat_id][user_id]['processing'] = False
            await process_next_in_queue(client, chat_id, user_id)
            return
        tracks = await get_audio_tracks(path)
        if not tracks:
            os.remove(path)
            await safe_telegram_call(client.edit_message_text, chat_id, msg.id, "No audio tracks found.")
            user_selections[chat_id][user_id]['processing'] = False
            await process_next_in_queue(client, chat_id, user_id)
            return
        user_selections[chat_id][user_id].update({
            'file_path': path,
            'selected_tracks': set(),
            'selected_subs': set(),
            'hard_sub': False,
            'resolution': 'original',
            'output_format': None,
            'status': 'Selecting audio tracks...',
            'last_percent': 0
        })
        await safe_telegram_call(client.edit_message_text, chat_id, msg.id, "Select audio tracks:", reply_markup=await create_track_selection_keyboard(chat_id, user_id, tracks))
    except Exception as e:
        logger.error(f"Error in handle_video_message: {str(e)}")
        user_selections[chat_id][user_id]['processing'] = False
        if os.path.exists(path): os.remove(path)
        await process_next_in_queue(client, chat_id, user_id)

def register_video_handlers(app: Client):
    @app.on_message(filters=filters.video | filters.document)
    async def handle_message(client: Client, message: Message):
        await handle_video_message(client, message)
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
            tracks = await get_audio_tracks(user_selections[chat_id][user_id]['file_path'])
            await safe_telegram_call(
                client.edit_message_text,
                chat_id,
                status_message_id,
                "Select audio tracks:",
                reply_markup=await create_track_selection_keyboard(chat_id, user_id, tracks)
            )
        elif data == "done_tracks":
            tracks = await get_subtitle_tracks(user_selections[chat_id][user_id]['file_path'])
            if not tracks:
                # No subtitles, skip to resolution
                user_selections[chat_id][user_id]['status'] = "Selecting resolution..."
                await safe_telegram_call(
                    client.edit_message_text,
                    chat_id,
                    status_message_id,
                    "Select resolution:",
                    reply_markup=await create_resolution_selection_keyboard()
                )
            else:
                user_selections[chat_id][user_id]['status'] = "Selecting subtitle tracks..."
                await safe_telegram_call(
                    client.edit_message_text,
                    chat_id,
                    status_message_id,
                    "Select subtitle tracks:",
                    reply_markup=await create_subtitle_selection_keyboard(chat_id, user_id, tracks)
                )
        elif data.startswith("sub_"):
            idx = int(data.split("_")[1])
            st = user_selections[chat_id][user_id]['selected_subs']
            st.remove(idx) if idx in st else st.add(idx)
            tracks = await get_subtitle_tracks(user_selections[chat_id][user_id]['file_path'])
            await safe_telegram_call(
                client.edit_message_text,
                chat_id,
                status_message_id,
                "Select subtitle tracks:",
                reply_markup=await create_subtitle_selection_keyboard(chat_id, user_id, tracks)
            )
        elif data == "toggle_hardsub":
            user_selections[chat_id][user_id]['hard_sub'] = not user_selections[chat_id][user_id]['hard_sub']
            tracks = await get_subtitle_tracks(user_selections[chat_id][user_id]['file_path'])
            await safe_telegram_call(
                client.edit_message_text,
                chat_id,
                status_message_id,
                "Select subtitle tracks:",
                reply_markup=await create_subtitle_selection_keyboard(chat_id, user_id, tracks)
            )
        elif data == "done_subs":
            user_selections[chat_id][user_id]['status'] = "Selecting resolution..."
            await safe_telegram_call(
                client.edit_message_text,
                chat_id,
                status_message_id,
                "Select resolution:",
                reply_markup=await create_resolution_selection_keyboard()
            )
        elif data.startswith("res_"):
            res = data.split("_")[1]
            user_selections[chat_id][user_id]['resolution'] = res
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
            await process_video(
                src, dst,
                list(info['selected_tracks']),
                list(info['selected_subs']),
                info['hard_sub'],
                info['resolution'],
                fmt
            )
            await generate_thumbnail(src, thumb)
            cap = info.get('default_caption', "Here is your video.")
            info['status'] = "Uploading video..."
            await safe_telegram_call(client.edit_message_text, chat_id, status_message_id, "Uploading video...")
            await upload_with_progress(client, chat_id, user_id, dst, cap, fmt, thumb, reply_to_message_id=info.get('original_message_id'))
            for f in [src, dst, thumb]:
                if os.path.exists(f): os.remove(f)
            user_selections[chat_id][user_id]['processing'] = False
            if 'file_path' in user_selections[chat_id][user_id]:
                del user_selections[chat_id][user_id]['file_path']
            info['status'] = "Completed"
            await safe_telegram_call(client.edit_message_text, chat_id, status_message_id, "Completed")
            await safe_telegram_call(cq.message.delete)
            await process_next_in_queue(client, chat_id, user_id)



# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------                