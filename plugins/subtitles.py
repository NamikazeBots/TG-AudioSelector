
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from config import DOWNLOAD_DIR
from utils import authorized_only, download_with_progress, run_ffmpeg
from queue_manager import queue_manager

@Client.on_message(filters.command("extract_sub"))
@authorized_only
async def extract_sub_cmd(client: Client, message: Message):
    rep = message.reply_to_message
    if not rep or not (rep.video or rep.document):
        await message.reply("Reply to a video.")
        return

    task = await queue_manager.add_task(message.from_user.id, message.chat.id, "Extract Sub", message)
    m = await message.reply(f"Extracting subtitles... Task ID: `{task.id}`. Waiting...")
    await task.ready_event.wait()

    if task.cancel_event.is_set():
        queue_manager.remove_task(task.id)
        await m.edit("Task cancelled.")
        return

    path, out = None, None
    try:
        path = os.path.join(DOWNLOAD_DIR, f"ext_s_{task.id}_{rep.id}.mp4")
        out = os.path.join(DOWNLOAD_DIR, f"sub_{task.id}_{rep.id}.srt")
        await download_with_progress(client, rep, path, message.chat.id, message.from_user.id, status_msg_id=m.id)
        await run_ffmpeg(['-y', '-i', path, '-map', '0:s:0', out])
        await client.send_document(message.chat.id, out, reply_to_message_id=rep.id)
    except Exception as e:
        await m.edit(f"Failed or no subs: {e}")
    finally:
        for f in [path, out]:
            if f and os.path.exists(f): os.remove(f)
        queue_manager.remove_task(task.id)
        try: await m.delete()
        except: pass

@Client.on_message(filters.command(["sub", "hsub"]))
@authorized_only
async def addsub_cmd(client: Client, message: Message):
    is_hard = message.command[0] == "hsub"
    rep = message.reply_to_message
    if not rep:
        await message.reply("Reply to a subtitle file (.srt) which is a reply to a video.")
        return

    vid_msg, sub_msg = None, None
    if rep.document and rep.document.file_name and rep.document.file_name.endswith((".srt", ".ass")):
        sub_msg = rep
        vid_msg = rep.reply_to_message

    if not vid_msg or not sub_msg or not (vid_msg.video or vid_msg.document):
        await message.reply("Could not find both video and subtitle. Make sure the subtitle is a reply to the video.")
        return

    task = await queue_manager.add_task(message.from_user.id, message.chat.id, "Add Sub", message)
    m = await message.reply(f"Adding {'hard' if is_hard else 'soft'} subtitles...")
    await task.ready_event.wait()

    if task.cancel_event.is_set():
        queue_manager.remove_task(task.id)
        await m.edit("Task cancelled.")
        return

    v_path, s_path, out = None, None, None
    try:
        v_path = os.path.join(DOWNLOAD_DIR, f"v_{task.id}.mp4")
        s_path = os.path.join(DOWNLOAD_DIR, f"s_{task.id}.srt")
        out = os.path.join(DOWNLOAD_DIR, f"out_{task.id}.mp4")
        await download_with_progress(client, vid_msg, v_path, message.chat.id, message.from_user.id, status_msg_id=m.id)
        await download_with_progress(client, sub_msg, s_path, message.chat.id, message.from_user.id, status_msg_id=m.id)
        if is_hard:
            await run_ffmpeg(['-y', '-i', v_path, '-vf', f"subtitles='{s_path}'", '-c:a', 'copy', out])
        else:
            await run_ffmpeg(['-y', '-i', v_path, '-i', s_path, '-c', 'copy', '-c:s', 'mov_text', out])
        await client.send_video(message.chat.id, out, reply_to_message_id=vid_msg.id)
    except Exception as e:
        await m.edit(f"Failed: {e}")
    finally:
        for f in [v_path, s_path, out]:
            if f and os.path.exists(f): os.remove(f)
        queue_manager.remove_task(task.id)
        try: await m.delete()
        except: pass

@Client.on_message(filters.command("rsub"))
@authorized_only
async def rsub_cmd(client: Client, message: Message):
    rep = message.reply_to_message
    if not rep or not (rep.video or rep.document):
        await message.reply("Reply to a video.")
        return

    task = await queue_manager.add_task(message.from_user.id, message.chat.id, "Rem Sub", message)
    m = await message.reply("Removing subtitles...")
    await task.ready_event.wait()

    if task.cancel_event.is_set():
        queue_manager.remove_task(task.id)
        await m.edit("Task cancelled.")
        return

    path, out = None, None
    try:
        path = os.path.join(DOWNLOAD_DIR, f"rs_{task.id}.mp4")
        out = os.path.join(DOWNLOAD_DIR, f"nosub_{task.id}.mp4")
        await download_with_progress(client, rep, path, message.chat.id, message.from_user.id, status_msg_id=m.id)
        await run_ffmpeg(['-y', '-i', path, '-sn', '-c:v', 'copy', '-c:a', 'copy', out])
        await client.send_video(message.chat.id, out, reply_to_message_id=rep.id)
    except Exception as e:
        await m.edit(f"Failed: {e}")
    finally:
        for f in [path, out]:
            if f and os.path.exists(f): os.remove(f)
        queue_manager.remove_task(task.id)
        try: await m.delete()
        except: pass
