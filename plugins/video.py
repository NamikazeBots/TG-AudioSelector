
import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatType
from config import DOWNLOAD_DIR, OWNER_ID
from database import db
from utils import (
    get_audio_tracks, download_with_progress, sanitize_filename,
    validate_video_file, check_daily_limit, authorized_only, user_selections,
    create_track_selection_keyboard
)
from queue_manager import queue_manager

logger = logging.getLogger(__name__)

@Client.on_message((filters.video | filters.document) & ~filters.command(["extract_audio", "extract_sub", "addaudio", "remaudio", "sub", "hsub", "rsub", "trim", "mediainfo", "merge", "Marge"]))
@authorized_only
async def handle_video(client: Client, message: Message):
    chat_id, user_id = message.chat.id, message.from_user.id
    if user_id != OWNER_ID and message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("This bot works only in groups.")
        return
    if not await check_daily_limit(user_id):
        await message.reply("Daily limit reached.")
        return

    # Add to queue
    task = await queue_manager.add_task(user_id, chat_id, "Video Processing", message)
    status_msg = await message.reply(f"Added to queue. Task ID: `{task.id}`. Waiting for turn...")

    await task.ready_event.wait()

    if task.cancel_event.is_set():
        queue_manager.remove_task(task.id)
        await status_msg.edit("Task cancelled.")
        return

    try:
        user_selections.setdefault(chat_id, {}).setdefault(user_id, {})
        user_selections[chat_id][user_id]['processing'] = True
        user_selections[chat_id][user_id]['status_message_id'] = status_msg.id

        name = message.video.file_name if message.video else message.document.file_name
        if not name: name = f"video_{message.id}.mp4"
        if db:
            settings = await db.get_all_user_settings(user_id)
            if 'default_name' in settings: name = settings['default_name']
            if 'default_caption' in settings: user_selections[chat_id][user_id]['default_caption'] = settings['default_caption']

        path = os.path.join(DOWNLOAD_DIR, f"{user_id}_{task.id}_{sanitize_filename(name)}")
        await download_with_progress(client, message, path, chat_id, user_id, status_msg_id=status_msg.id, notify_selection=True)

        if not validate_video_file(path):
            await status_msg.edit("Invalid video file.")
            return

        tracks = get_audio_tracks(path)
        if not tracks:
            await status_msg.edit("No audio tracks found.")
            return

        user_selections[chat_id][user_id].update({
            'file_path': path,
            'selected_tracks': set(),
            'task_id': task.id,
            'status': 'Selecting tracks...'
        })

        await status_msg.edit("Select tracks:", reply_markup=await create_track_selection_keyboard(chat_id, user_id, tracks))

    except Exception as e:
        logger.error(f"Error handling video: {e}")
        await status_msg.edit(f"Error: {e}")
        if 'path' in locals() and os.path.exists(path): os.remove(path)
        queue_manager.remove_task(task.id)
