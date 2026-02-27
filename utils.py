# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
from collections import defaultdict
import os
import shutil
import ffmpeg
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from tqdm import tqdm
import logging
import asyncio
import re
from datetime import datetime, timedelta
from config import DOWNLOAD_DIR, MAX_FILE_SIZE, PREMIUM_USERS, DAILY_LIMIT_FREE, DAILY_LIMIT_PREMIUM, OWNER_ID, DB_CHANNEL_ID
from functools import wraps
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
# Thread-safe storage
user_selections = defaultdict(lambda: defaultdict(dict))
status_messages = {}
daily_limits = defaultdict(lambda: {'count': 0, 'last_reset': datetime.now()})
last_update_time = defaultdict(lambda: 0)
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
def cleanup_downloads():
    if os.path.exists(DOWNLOAD_DIR):
        for filename in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f'Failed to delete {file_path}. Reason: {e}')
    else:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def sanitize_filename(filename: str) -> str:
    if not isinstance(filename, str):
        filename = str(filename) if filename is not None else "default_video"
    return re.sub(r'[^\w\-\.]', '_', filename)

def validate_video_file(file_path: str) -> bool:
    try:
        probe = ffmpeg.probe(file_path)
        return any(stream['codec_type'] == 'video' for stream in probe['streams'])
    except Exception as e:
        logger.error(f"File validation failed for {file_path}: {str(e)}")
        return False
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
def get_audio_tracks(input_file: str):
    try:
        probe = ffmpeg.probe(input_file)
        audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']
        tracks = []
        for idx, stream in enumerate(audio_streams):
            track_name = stream.get('tags', {}).get('language', f"Track {idx}")
            if 'title' in stream.get('tags', {}):
                track_name += f" ({stream['tags']['title']})"
            tracks.append((idx, track_name))
        return tracks
    except Exception as e:
        logger.error(f"Error probing file {input_file}: {str(e)}")
        raise
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
async def run_ffmpeg(args: list):
    process = await asyncio.create_subprocess_exec(
        'ffmpeg', *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        logger.error(f"FFmpeg failed with return code {process.returncode}")
        logger.error(f"Stderr: {stderr.decode()}")
        raise Exception(f"FFmpeg failed: {stderr.decode()}")
    return stdout, stderr

async def select_audio_tracks(input_file: str, output_file: str, selected_indices: list, output_format: str, resolution: str = None):
    try:
        # Construct FFmpeg command manually for better control and async execution
        args = ['-i', input_file, '-map', '0:v:0']

        # Scaling if resolution is provided
        if resolution:
            res_map = {"480p": "854:480", "720p": "1280:720", "1080p": "1920:1080"}
            scale = res_map.get(resolution)
            if scale:
                args.extend(['-vf', f'scale={scale}', '-c:v', 'libx264', '-preset', 'veryfast'])
            else:
                args.extend(['-c:v', 'copy'])
        else:
            args.extend(['-c:v', 'copy'])

        for idx in selected_indices:
            args.extend(['-map', f'0:a:{idx}'])

        args.extend(['-c:a', 'copy'])

        if output_format == "mkv":
            args.extend(['-f', 'matroska'])

        args.append(output_file)
        args.insert(0, '-y') # Overwrite output

        await run_ffmpeg(args)
    except Exception as e:
        logger.error(f"Error processing file {input_file}: {str(e)}")
        raise

async def generate_thumbnail(input_file: str, output_path: str):
    try:
        args = ['-y', '-ss', '00:00:01', '-i', input_file, '-vframes', '1', '-f', 'image2', output_path]
        await run_ffmpeg(args)
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {str(e)}")
        raise
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
async def check_daily_limit(user_id: int) -> bool:
    from database import db
    limit = DAILY_LIMIT_PREMIUM if user_id in PREMIUM_USERS else DAILY_LIMIT_FREE

    if db:
        count = await db.get_daily_count(user_id)
        if count >= limit:
            return False
        await db.increment_daily_count(user_id)
        return True
    else:
        now = datetime.now()
        user_data = daily_limits[user_id]
        if now - user_data['last_reset'] > timedelta(days=1):
            user_data['count'] = 0
            user_data['last_reset'] = now
        if user_data['count'] >= limit:
            return False
        user_data['count'] += 1
        return True
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
async def safe_telegram_call(func, *args, **kwargs):
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        if "FLOOD_WAIT" in str(e):
            wait_time = int(str(e).split("A wait of ")[1].split(" seconds")[0])
            logger.warning(f"Flood wait for {wait_time}s")
            await asyncio.sleep(wait_time)
            return await func(*args, **kwargs)
        raise
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
async def download_with_progress(client: Client, message: Message, file_path: str, chat_id: int, user_id: int):
    try:
        file_size = message.video.file_size if message.video else message.document.file_size
        if file_size and file_size > MAX_FILE_SIZE:
            raise ValueError(f"File too large: {file_size} bytes")
        bar, last_percent = None, user_selections[chat_id][user_id].get('last_percent', 0)
        status_message_id = user_selections[chat_id][user_id].get('status_message_id')
        async def progress(cur, total):
            nonlocal bar, last_percent
            if not bar: bar = tqdm(total=total, unit='B', unit_scale=True, desc=f"Downloading {user_id}", leave=False)
            bar.n = cur; bar.refresh()
            percent = int((cur / total) * 100)
            if percent >= last_percent + 5 or cur == total:
                last_percent = percent
                user_selections[chat_id][user_id]['last_percent'] = percent
                pbar = "█" * (percent//5) + " " * (20-percent//5)
                await safe_telegram_call(
                    client.edit_message_text,
                    chat_id,
                    status_message_id,
                    f"Downloading: [{pbar} {percent}%]"
                )
            if cur == total: bar.close()
        await client.download_media(message, file_path, progress=progress)
        # Notify user after download completes
        user = await client.get_users(user_id)
        user_name = user.username if user.username else user.first_name
        await safe_telegram_call(
            client.send_message,
            chat_id,
            f"@{user_name} your media has been downloaded, now select the tracks.",
            reply_to_message_id=message.id
        )
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        await safe_telegram_call(
            client.edit_message_text,
            chat_id,
            status_message_id,
            f"Download failed: {str(e)}"
        )
        raise
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
async def upload_with_progress(client: Client, chat_id: int, user_id: int, file_path: str, caption: str, output_format: str, thumb: str = None, reply_to_message_id: int = None):
    try:
        bar, last_percent = None, user_selections[chat_id][user_id].get('last_percent', 0)
        async def progress(cur, total):
            nonlocal bar, last_percent
            if not bar: bar = tqdm(total=total, unit='B', unit_scale=True, desc=f"Uploading {user_id}", leave=False)
            bar.n = cur; bar.refresh()
            percent = int((cur / total) * 100)
            if percent >= last_percent + 5 or cur == total:
                last_percent = percent
                user_selections[chat_id][user_id]['last_percent'] = percent
                pbar = "█" * (percent//5) + " " * (20-percent//5)
                await update_status_message(client, chat_id, user_id, f"Uploading: [{pbar} {percent}%]")
            if cur == total: bar.close()
        if output_format == "video":
            sent_msg = await safe_telegram_call(client.send_video, chat_id, file_path, caption=caption, progress=progress, thumb=thumb if thumb and os.path.exists(thumb) else None, reply_to_message_id=reply_to_message_id)
        else:
            sent_msg = await safe_telegram_call(client.send_document, chat_id, file_path, caption=caption, progress=progress, thumb=thumb if thumb and os.path.exists(thumb) else None, reply_to_message_id=reply_to_message_id)

        # Forward to DB Channel if configured
        if DB_CHANNEL_ID and sent_msg:
            try:
                # Use file_id for efficient forwarding
                file_id = sent_msg.video.file_id if output_format == "video" else sent_msg.document.file_id
                if output_format == "video":
                    await client.send_video(DB_CHANNEL_ID, file_id, caption=f"User: {user_id}\n\n{caption}")
                else:
                    await client.send_document(DB_CHANNEL_ID, file_id, caption=f"User: {user_id}\n\n{caption}")
            except Exception as e:
                logger.error(f"Failed to forward to DB Channel: {str(e)}")

    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        await update_status_message(client, chat_id, user_id, f"Upload failed: {str(e)}")
        raise

async def update_status_message(client: Client, chat_id: int, user_id: int, status: str, force_update: bool = False):
    try:
        now = datetime.now().timestamp()
        if not force_update and now - last_update_time[chat_id] < 5:  # Reduced from 10 to 5 seconds
            return
        last_update_time[chat_id] = now
        user_selections[chat_id][user_id]['status'] = status
        status_text = "\n".join(
            f"User {uid}: {user_selections[chat_id][uid].get('status','Idle')}"
            for uid in user_selections[chat_id] if isinstance(user_selections[chat_id][uid], dict)
        )
        if chat_id in status_messages:
            await safe_telegram_call(client.edit_message_text, chat_id, status_messages[chat_id], f"Current Status:\n{status_text}")
        else:
            msg = await safe_telegram_call(client.send_message, chat_id, f"Current Status:\n{status_text}")
            status_messages[chat_id] = msg.id
    except Exception as e:
        logger.error(f"Status update failed: {str(e)}")

async def create_track_selection_keyboard(chat_id: int, user_id: int, tracks: list):
    buttons = [[InlineKeyboardButton(f"{'✅ ' if idx in user_selections[chat_id][user_id].get('selected_tracks', set()) else ''}{name}", callback_data=f"track_{idx}") for idx, name in tracks]]
    buttons.append([InlineKeyboardButton("Done", callback_data="done_tracks")])
    return InlineKeyboardMarkup(buttons)

async def create_format_selection_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Video (MP4)", callback_data="format_video")],
        [InlineKeyboardButton("Document (MKV)", callback_data="format_mkv")]
    ])

def authorized_only(func):
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        from database import db
        user_id = message.from_user.id
        chat_id = message.chat.id

        if user_id == OWNER_ID:
            return await func(client, message, *args, **kwargs)

        authorized = False
        if db:
            authorized = await db.is_auth(chat_id)
        else:
            from config import ALLOWED_GROUP_IDS
            authorized = chat_id in ALLOWED_GROUP_IDS

        if not authorized:
            await safe_telegram_call(message.reply, "This bot is not authorized here.")
            return

        return await func(client, message, *args, **kwargs)
    return wrapper
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------