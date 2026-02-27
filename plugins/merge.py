
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from config import DOWNLOAD_DIR
from utils import authorized_only, user_selections, download_with_progress, run_ffmpeg
from queue_manager import queue_manager

@Client.on_message(filters.command(["merge", "Marge"]))
@authorized_only
async def merge_cmd(client: Client, message: Message):
    chat_id, user_id = message.chat.id, message.from_user.id

    # Check if user wants to add a file to merge list
    if message.reply_to_message and (message.reply_to_message.video or message.reply_to_message.document):
        user_selections.setdefault(chat_id, {}).setdefault(user_id, {}).setdefault('merge_files', []).append(message.reply_to_message)
        await message.reply(f"Added to merge list. Current count: {len(user_selections[chat_id][user_id]['merge_files'])}. Use `/merge now` to start merging.")
        return

    # Check if user wants to start merging
    if len(message.command) > 1 and message.command[1] == "now":
        files_to_merge = user_selections.get(chat_id, {}).get(user_id, {}).get('merge_files', [])
        if len(files_to_merge) < 2:
            await message.reply("Need at least 2 files to merge.")
            return
    else:
        await message.reply("Reply to a video with `/merge` to add it to the list, then use `/merge now` to merge them.")
        return

    task = await queue_manager.add_task(user_id, chat_id, "Merge", message)
    m = await message.reply(f"Merging {len(files_to_merge)} files...")
    await task.ready_event.wait()

    if task.cancel_event.is_set():
        queue_manager.remove_task(task.id)
        await m.edit("Task cancelled.")
        return

    paths, list_path, out = [], None, None
    try:
        for i, f_msg in enumerate(files_to_merge):
            p = os.path.join(DOWNLOAD_DIR, f"m_{task.id}_{i}.mp4")
            await download_with_progress(client, f_msg, p, chat_id, user_id, status_msg_id=m.id)
            paths.append(p)

        # Create concat file
        list_path = os.path.join(DOWNLOAD_DIR, f"list_{task.id}.txt")
        with open(list_path, 'w') as f:
            for p in paths:
                f.write(f"file '{os.path.abspath(p)}'\n")

        out = os.path.join(DOWNLOAD_DIR, f"merged_{task.id}.mp4")
        await run_ffmpeg(['-y', '-f', 'concat', '-safe', '0', '-i', list_path, '-c', 'copy', out])
        await client.send_video(chat_id, out)
    except Exception as e:
        await m.edit(f"Failed: {e}")
    finally:
        for f in paths + [list_path, out]:
            if f and os.path.exists(f): os.remove(f)
        if user_id in user_selections.get(chat_id, {}) and 'merge_files' in user_selections[chat_id][user_id]:
            user_selections[chat_id][user_id]['merge_files'] = []
        queue_manager.remove_task(task.id)
        try: await m.delete()
        except: pass
