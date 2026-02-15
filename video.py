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
        if isinstance(nxt, Message):
            await handle_video_message(client, nxt)
        elif isinstance(nxt, dict) and 'local_path' in nxt:
            await process_local_video(client, chat_id, user_id, nxt['local_path'], nxt['original_name'])

async def process_zip_file(client: Client, message: Message, path: str):
    chat_id, user_id = message.chat.id, message.from_user.id
    temp_extract_dir = os.path.join(DOWNLOAD_DIR, f"extract_{user_id}_{message.id}")
    os.makedirs(temp_extract_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)

        # Process each file in the zip
        found_videos = False
        for root, dirs, files in os.walk(temp_extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if await validate_video_file(file_path):
                    found_videos = True
                    # Move to a stable location immediately
                    stable_path = os.path.join(DOWNLOAD_DIR, f"zip_{user_id}_{sanitize_filename(file)}")
                    shutil.move(file_path, stable_path)

                    user_selections[chat_id][user_id]['queue'].append({
                        'local_path': stable_path,
                        'original_name': file
                    })

        if found_videos:
            await safe_telegram_call(client.send_message, chat_id, f"Found {len(user_selections[chat_id][user_id]['queue'])} video(s) in zip. Processing will start shortly.")
        else:
            await safe_telegram_call(client.send_message, chat_id, "No valid video files found in the zip.")

    except Exception as e:
        logger.error(f"Error processing zip: {str(e)}")
        await safe_telegram_call(client.send_message, chat_id, f"Error processing zip: {str(e)}")
    finally:
        shutil.rmtree(temp_extract_dir, ignore_errors=True)
        if os.path.exists(path): os.remove(path)

async def process_local_video(client: Client, chat_id: int, user_id: int, path: str, original_name: str):
    # Load user settings from DB
    from database import db
    user_config = await db.get_user_settings(user_id)

    # This mirrors handle_video_message but for a local file
    name = original_name
    if 'default_name' in user_config:
        name = user_config['default_name']

    stable_path = os.path.join(DOWNLOAD_DIR, f"{user_id}_{sanitize_filename(name)}")
    if path != stable_path:
        shutil.move(path, stable_path)

    user_selections.setdefault(chat_id, {}).setdefault(user_id, {'processing': True, 'queue': []})
    user_selections[chat_id][user_id]['processing'] = True
    # Update in-memory from DB
    if 'default_name' in user_config: user_selections[chat_id][user_id]['default_name'] = user_config['default_name']
    if 'default_caption' in user_config: user_selections[chat_id][user_id]['default_caption'] = user_config['default_caption']

    msg = await safe_telegram_call(client.send_message, chat_id, f"Processing {original_name}. Analyzing tracks...")
    user_selections[chat_id][user_id]['status_message_id'] = msg.id

    tracks = await get_audio_tracks(stable_path)
    if not tracks:
        if os.path.exists(stable_path): os.remove(stable_path)
        await safe_telegram_call(msg.edit_text, f"No audio tracks found in {original_name}.")
        user_selections[chat_id][user_id]['processing'] = False
        await process_next_in_queue(client, chat_id, user_id)
        return

    user_selections[chat_id][user_id].update({
        'file_path': stable_path,
        'selected_tracks': set(),
        'selected_subs': set(),
        'hard_sub': False,
        'resolution': 'original',
        'output_format': None,
        'status': f'Selecting tracks for {original_name}...',
        'last_percent': 0
    })
    await safe_telegram_call(msg.edit_text, f"Select audio tracks for {original_name}:", reply_markup=await create_track_selection_keyboard(chat_id, user_id, tracks))

async def handle_video_message(client: Client, message: Message):
    chat_id, user_id = message.chat.id, message.from_user.id

    # Check if user is in merge mode
    from utils import merge_files
    if user_id in merge_files.get(chat_id, {}):
        return

    from database import db
    if user_id != OWNER_ID and not await db.is_authorized(chat_id) and chat_id not in ALLOWED_GROUP_IDS:
        logger.info(f"Unauthorized access attempt: user_id={user_id}, chat_id={chat_id}")
        await safe_telegram_call(message.reply, "This bot is not authorized here.")
        return
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
        await safe_telegram_call(message.reply, "Please send a video or zip file.")
        return

    is_zip = False
    if message.document and message.document.file_name and message.document.file_name.endswith(".zip"):
        is_zip = True

    size = message.video.file_size if message.video else message.document.file_size
    if size and size > MAX_FILE_SIZE:
        await safe_telegram_call(message.reply, f"File size exceeds {MAX_FILE_SIZE} bytes")
        return
    # Load user settings from DB
    user_config = await db.get_user_settings(user_id)

    name = message.video.file_name if message.video else message.document.file_name
    if not name:
        name = f"video_{message.id}.mp4"

    if 'default_name' in user_config:
        name = user_config['default_name']
    elif user_id in user_selections.get(chat_id, {}) and 'default_name' in user_selections[chat_id][user_id]:
        name = user_selections[chat_id][user_id]['default_name']

    path = os.path.join(DOWNLOAD_DIR, f"{user_id}_{sanitize_filename(name)}")
    user_selections.setdefault(chat_id, {}).setdefault(user_id, {'processing': True, 'queue': [], 'original_message_id': message.id})
    # Update in-memory from DB
    if 'default_name' in user_config: user_selections[chat_id][user_id]['default_name'] = user_config['default_name']
    if 'default_caption' in user_config: user_selections[chat_id][user_id]['default_caption'] = user_config['default_caption']
    user_selections[chat_id][user_id]['status'] = "Starting download..."
    msg = await safe_telegram_call(message.reply, "Starting download...")
    user_selections[chat_id][user_id]['status_message_id'] = msg.id
    try:
        await download_with_progress(client, message, path, chat_id, user_id)

        if is_zip:
            await safe_telegram_call(msg.edit_text, "Extracting zip file...")
            user_selections[chat_id][user_id]['processing'] = False # Zip handler will manage processing flag for individual files
            await process_zip_file(client, message, path)
            await process_next_in_queue(client, chat_id, user_id)
            return

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