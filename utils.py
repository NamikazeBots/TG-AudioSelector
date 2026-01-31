# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
from collections import defaultdict
import os
import ffmpeg
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from tqdm import tqdm
import logging
import asyncio
import re
from datetime import datetime, timedelta
from config import DOWNLOAD_DIR, MAX_FILE_SIZE, PREMIUM_USERS, DAILY_LIMIT_FREE, DAILY_LIMIT_PREMIUM, DB_CHANNEL_ID, ALLOWED_GROUP_IDS
from database import db
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
merge_files = defaultdict(lambda: defaultdict(list))
status_messages = {}
# daily_limits = defaultdict(lambda: {'count': 0, 'last_reset': datetime.now()}) # Moved to DB
last_update_time = defaultdict(lambda: 0)
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
def sanitize_filename(filename: str) -> str:
    if not isinstance(filename, str):
        filename = str(filename) if filename is not None else "default_video"
    return re.sub(r'[^\w\-\.]', '_', filename)

async def validate_video_file(file_path: str) -> bool:
    try:
        probe = await asyncio.to_thread(ffmpeg.probe, file_path)
        return any(stream['codec_type'] == 'video' for stream in probe['streams'])
    except Exception as e:
        logger.error(f"File validation failed for {file_path}: {str(e)}")
        return False
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
async def get_audio_tracks(input_file: str):
    try:
        probe = await asyncio.to_thread(ffmpeg.probe, input_file)
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

async def get_subtitle_tracks(input_file: str):
    try:
        probe = await asyncio.to_thread(ffmpeg.probe, input_file)
        subtitle_streams = [s for s in probe['streams'] if s['codec_type'] == 'subtitle']
        tracks = []
        for idx, stream in enumerate(subtitle_streams):
            track_name = stream.get('tags', {}).get('language', f"Subtitle {idx}")
            if 'title' in stream.get('tags', {}):
                track_name += f" ({stream['tags']['title']})"
            tracks.append((idx, track_name))
        return tracks
    except Exception as e:
        logger.error(f"Error probing subtitles in {input_file}: {str(e)}")
        return []

async def get_media_info(file_path: str):
    try:
        probe = await asyncio.to_thread(ffmpeg.probe, file_path)
        format_info = probe.get('format', {})
        streams = probe.get('streams', [])

        info = f"**File Info:**\n"
        info += f"Filename: {os.path.basename(format_info.get('filename', 'Unknown'))}\n"
        info += f"Size: {int(format_info.get('size', 0)) / (1024*1024):.2f} MB\n"
        info += f"Duration: {float(format_info.get('duration', 0)):.2f}s\n"

        for i, stream in enumerate(streams):
            info += f"\n**Stream {i} ({stream.get('codec_type')}):**\n"
            info += f"Codec: {stream.get('codec_name')}\n"
            if stream.get('codec_type') == 'video':
                info += f"Resolution: {stream.get('width')}x{stream.get('height')}\n"
            elif stream.get('codec_type') == 'audio':
                info += f"Channels: {stream.get('channels')}\n"
                info += f"Language: {stream.get('tags', {}).get('language', 'Unknown')}\n"
                if 'title' in stream.get('tags', {}):
                    info += f"Title: {stream['tags']['title']}\n"
            elif stream.get('codec_type') == 'subtitle':
                info += f"Language: {stream.get('tags', {}).get('language', 'Unknown')}\n"
                if 'title' in stream.get('tags', {}):
                    info += f"Title: {stream['tags']['title']}\n"

        return info
    except Exception as e:
        logger.error(f"Error getting media info: {str(e)}")
        return f"Error getting media info: {str(e)}"
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
async def process_video(input_file: str, output_file: str, selected_audio: list, selected_subs: list, hard_sub: bool, resolution: str, output_format: str):
    def _run():
        try:
            inp = ffmpeg.input(input_file)
            v = inp.video

            needs_reencode = False

            # Apply resolution scaling
            if resolution != 'original':
                needs_reencode = True
                height = int(resolution.replace('p', ''))
                v = v.filter('scale', -2, height)

            # Apply hard subs
            if hard_sub and selected_subs:
                needs_reencode = True
                sub_idx = selected_subs[0]
                # Specific escaping for subtitles filter filename
                # Colons must be escaped, and the whole path might need single quotes if it has spaces
                # But FFmpeg's subtitles filter is notoriously picky about this.
                escaped_input = input_file.replace("\\", "/").replace(":", "\\:").replace("'", "'\\\\\\''")
                v = v.filter('subtitles', escaped_input, si=sub_idx)

            # Audio streams
            a_streams = [inp[f'a:{i}'] for i in selected_audio]

            # Subtitle streams (soft subs for MKV)
            s_streams = []
            if not hard_sub and output_format == "mkv":
                s_streams = [inp[f's:{i}'] for i in selected_subs]

            # Output arguments
            output_args = {}
            if needs_reencode:
                output_args['c:v'] = 'libx264'
                output_args['preset'] = 'veryfast'
                output_args['crf'] = '23'
            else:
                output_args['c:v'] = 'copy'

            output_args['c:a'] = 'copy'
            if s_streams:
                output_args['c:s'] = 'copy'

            if output_format == "mkv":
                output_args['f'] = 'matroska'

            ffmpeg.output(v, *a_streams, *s_streams, output_file, **output_args).run(overwrite_output=True)
        except Exception as e:
            logger.error(f"Error processing video {input_file}: {str(e)}")
            raise

    await asyncio.to_thread(_run)

async def merge_files_ffmpeg(files: list, output_file: str):
    def _run():
        try:
            probes = [ffmpeg.probe(f) for f in files]
            video_counts = [len([s for s in p['streams'] if s['codec_type'] == 'video']) for p in probes]

            if sum(video_counts) > 1 and all(vc > 0 for vc in video_counts):
                # Multiple videos: join them (concatenation)
                inputs = [ffmpeg.input(f) for f in files]

                # To concatenate diverse videos, we need to scale them to a common resolution
                # Let's use the resolution of the first video
                first_v = next(s for s in probes[0]['streams'] if s['codec_type'] == 'video')
                target_w, target_h = first_v['width'], first_v['height']

                v_streams = [i.video.filter('scale', target_w, target_h).filter('setsar', 1) for i in inputs]
                a_streams = []
                for i, p in enumerate(probes):
                    if any(s['codec_type'] == 'audio' for s in p['streams']):
                        a_streams.append(inputs[i].audio)
                    else:
                        # Add silent audio if missing to keep stream count consistent
                        # This is more complex in ffmpeg-python, but we'll try to find at least one audio
                        pass

                # If all have audio, join them
                if len(a_streams) == len(v_streams):
                    joined = ffmpeg.concat(*[s for pair in zip(v_streams, a_streams) for s in pair], v=1, a=1).node
                    ffmpeg.output(joined[0], joined[1], output_file, vcodec='libx264', preset='veryfast', acodec='aac').run(overwrite_output=True)
                else:
                    # Join only video and use first audio found
                    joined_v = ffmpeg.concat(*v_streams, v=1, a=0).node[0]
                    if a_streams:
                        ffmpeg.output(joined_v, a_streams[0], output_file, vcodec='libx264', preset='veryfast', acodec='aac').run(overwrite_output=True)
                    else:
                        ffmpeg.output(joined_v, output_file, vcodec='libx264', preset='veryfast').run(overwrite_output=True)
            else:
                # Mux video with other streams
                inputs = [ffmpeg.input(f) for f in files]
                ffmpeg.output(*inputs, output_file, c='copy').run(overwrite_output=True)
        except Exception as e:
            logger.error(f"Error merging files: {str(e)}")
            raise
    await asyncio.to_thread(_run)

async def generate_thumbnail(input_file: str, output_path: str):
    def _run():
        try:
            ffmpeg.input(input_file, ss='00:00:01').output(output_path, vframes=1, format='image2').run(overwrite_output=True)
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {str(e)}")
            raise
    await asyncio.to_thread(_run)
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------
async def check_daily_limit(user_id: int) -> bool:
    now = datetime.now()
    user_data = await db.get_daily_limit(user_id)
    if now - user_data['last_reset'] > timedelta(days=1):
        user_data['count'] = 0
        user_data['last_reset'] = now
    limit = DAILY_LIMIT_PREMIUM if user_id in PREMIUM_USERS else DAILY_LIMIT_FREE
    if user_data['count'] >= limit:
        return False
    user_data['count'] += 1
    await db.update_daily_limit(user_id, user_data['count'], user_data['last_reset'])
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

        # Forward to DB Channel
        if DB_CHANNEL_ID and sent_msg:
            try:
                await sent_msg.forward(DB_CHANNEL_ID)
            except Exception as fe:
                logger.error(f"Failed to forward to DB channel: {str(fe)}")

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
    selected = user_selections[chat_id][user_id].get('selected_tracks', set())
    buttons = []
    for idx, name in tracks:
        buttons.append([InlineKeyboardButton(f"{'✅ ' if idx in selected else ''}{name}", callback_data=f"track_{idx}")])
    buttons.append([InlineKeyboardButton("Done", callback_data="done_tracks")])
    return InlineKeyboardMarkup(buttons)

async def create_subtitle_selection_keyboard(chat_id: int, user_id: int, tracks: list):
    selected = user_selections[chat_id][user_id].get('selected_subs', set())
    buttons = []
    for idx, name in tracks:
        buttons.append([InlineKeyboardButton(f"{'✅ ' if idx in selected else ''}{name}", callback_data=f"sub_{idx}")])

    hard_sub = user_selections[chat_id][user_id].get('hard_sub', False)
    buttons.append([InlineKeyboardButton(f"Hard Sub: {'ON' if hard_sub else 'OFF'}", callback_data="toggle_hardsub")])
    buttons.append([InlineKeyboardButton("Done", callback_data="done_subs")])
    return InlineKeyboardMarkup(buttons)

async def create_format_selection_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Video (MP4)", callback_data="format_video")],
        [InlineKeyboardButton("Document (MKV)", callback_data="format_mkv")]
    ])

async def create_resolution_selection_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Original", callback_data="res_original")],
        [InlineKeyboardButton("1080p", callback_data="res_1080p")],
        [InlineKeyboardButton("720p", callback_data="res_720p")],
        [InlineKeyboardButton("480p", callback_data="res_480p")]
    ])
# ----------------------------------------
# 𝐌𝐀𝐃𝐄 𝐁𝐘 𝐀𝐁𝐇𝐈
# 𝐓𝐆 𝐈𝐃 : @𝐂𝐋𝐔𝐓𝐂𝐇𝟎𝟎𝟖
# 𝐀𝐍𝐘 𝐈𝐒𝐒𝐔𝐄𝐒 𝐎𝐑 𝐀𝐃𝐃𝐈𝐍𝐆 𝐌𝐎𝐑𝐄 𝐓𝐇𝐈𝐍𝐆𝐬 𝐂𝐀𝐍 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐌𝐄
# ----------------------------------------