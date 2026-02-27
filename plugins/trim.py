
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from config import DOWNLOAD_DIR
from utils import authorized_only, download_with_progress, run_ffmpeg
from queue_manager import queue_manager

@Client.on_message(filters.command("trim"))
@authorized_only
async def trim_cmd(client: Client, message: Message):
    rep = message.reply_to_message
    if not rep or not (rep.video or rep.document):
        await message.reply("Reply to a video.")
        return
    if len(message.command) < 3:
        await message.reply("Usage: /trim HH:MM:SS HH:MM:SS (Start End)")
        return
    start_t, end_t = message.command[1], message.command[2]

    task = await queue_manager.add_task(message.from_user.id, message.chat.id, "Trim", message)
    m = await message.reply("Trimming video...")
    await task.ready_event.wait()

    if task.cancel_event.is_set():
        queue_manager.remove_task(task.id)
        await m.edit("Task cancelled.")
        return

    path, out = None, None
    try:
        path = os.path.join(DOWNLOAD_DIR, f"tr_{task.id}.mp4")
        out = os.path.join(DOWNLOAD_DIR, f"trimmed_{task.id}.mp4")
        await download_with_progress(client, rep, path, message.chat.id, message.from_user.id, status_msg_id=m.id)
        await run_ffmpeg(['-y', '-i', path, '-ss', start_t, '-to', end_t, '-c', 'copy', out])
        await client.send_video(message.chat.id, out, reply_to_message_id=rep.id)
    except Exception as e:
        await m.edit(f"Failed: {e}")
    finally:
        for f in [path, out]:
            if f and os.path.exists(f): os.remove(f)
        queue_manager.remove_task(task.id)
        try: await m.delete()
        except: pass
