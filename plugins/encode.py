
import os
import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import DOWNLOAD_DIR
from utils import (
    get_audio_tracks, select_audio_tracks, upload_with_progress,
    create_track_selection_keyboard, user_selections, generate_thumbnail
)
from queue_manager import queue_manager

logger = logging.getLogger(__name__)

@Client.on_callback_query()
async def handle_callbacks(client: Client, cq: CallbackQuery):
    chat_id, user_id = cq.message.chat.id, cq.from_user.id
    if user_id not in user_selections.get(chat_id, {}):
        # Allow some general callbacks even if session not in user_selections
        if cq.data in ["about", "back", "close"]:
            return # Let start.py handle it
        await cq.answer("Session not found.", show_alert=True)
        return

    data = cq.data
    info = user_selections[chat_id][user_id]

    if data.startswith("track_"):
        idx = int(data.split("_")[1])
        st = info['selected_tracks']
        if idx in st: st.remove(idx)
        else: st.add(idx)
        tracks = get_audio_tracks(info['file_path'])
        await cq.message.edit_reply_markup(reply_markup=await create_track_selection_keyboard(chat_id, user_id, tracks))

    elif data == "done_tracks":
        if not info['selected_tracks']:
            await cq.answer("Select at least one track!", show_alert=True)
            return
        await cq.message.edit_text("Select output format and resolution:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("MP4 - 480p", callback_data="proc_mp4_480p"), InlineKeyboardButton("MP4 - 720p", callback_data="proc_mp4_720p")],
            [InlineKeyboardButton("MP4 - 1080p", callback_data="proc_mp4_1080p"), InlineKeyboardButton("MP4 - Original", callback_data="proc_mp4_none")],
            [InlineKeyboardButton("MKV - Original", callback_data="proc_mkv_none")]
        ]))

    elif data.startswith("proc_"):
        parts = data.split("_")
        fmt, res = parts[1], parts[2]
        if res == "none": res = None

        src = info['file_path']
        outname = info.get('default_name') or f"proc_{os.path.basename(src)}"
        dst = os.path.join(DOWNLOAD_DIR, f"final_{user_id}_{outname}")
        if fmt == "mkv": dst = os.path.splitext(dst)[0] + ".mkv"
        else: dst = os.path.splitext(dst)[0] + ".mp4"

        thumb = dst + ".jpg"
        await cq.message.edit_text(f"Processing ({fmt}, {res or 'original'})...")

        try:
            await select_audio_tracks(src, dst, list(info['selected_tracks']), fmt, res)
            await generate_thumbnail(dst, thumb)
            cap = info.get('default_caption', "Here is your video.")
            await upload_with_progress(client, chat_id, user_id, dst, cap, "video" if fmt=="mp4" else "mkv", thumb, reply_to_message_id=cq.message.reply_to_message_id)
        except Exception as e:
            await cq.message.edit_text(f"Processing failed: {e}")
        finally:
            for f in [src, dst, thumb]:
                if os.path.exists(f): os.remove(f)
            queue_manager.remove_task(info['task_id'])
            del user_selections[chat_id][user_id]
            await cq.message.delete()
