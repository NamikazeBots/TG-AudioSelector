
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from config import DOWNLOAD_DIR
from utils import authorized_only, download_with_progress, run_ffmpeg
from queue_manager import queue_manager

@Client.on_message(filters.command("extract_audio"))
@authorized_only
async def extract_audio_cmd(client: Client, message: Message):
    rep = message.reply_to_message
    if not rep or not (rep.video or rep.document):
        await message.reply("Reply to a video.")
        return

    task = await queue_manager.add_task(message.from_user.id, message.chat.id, "Extract Audio", message)
    m = await message.reply(f"Extracting audio... Task ID: `{task.id}`. Waiting...")
    await task.ready_event.wait()

    path = os.path.join(DOWNLOAD_DIR, f"ext_a_{task.id}_{rep.id}.mp4")
    out = os.path.join(DOWNLOAD_DIR, f"audio_{task.id}_{rep.id}.mp3")
    try:
        await download_with_progress(client, rep, path, message.chat.id, message.from_user.id, status_msg_id=m.id)
        await run_ffmpeg(['-y', '-i', path, '-vn', '-acodec', 'libmp3lame', out])
        await client.send_audio(message.chat.id, out, reply_to_message_id=rep.id)
    except Exception as e:
        await m.edit(f"Failed: {e}")
    finally:
        for f in [path, out]:
            if os.path.exists(f): os.remove(f)
        queue_manager.remove_task(task.id)
        await m.delete()

@Client.on_message(filters.command("addaudio"))
@authorized_only
async def addaudio_cmd(client: Client, message: Message):
    rep = message.reply_to_message
    if not rep:
        await message.reply("Reply to an audio file with /addaudio while that audio is a reply to a video, OR reply to a video with /addaudio while sending/replying to an audio.")
        return

    vid_msg, aud_msg = None, None
    if rep.audio:
        aud_msg = rep
        vid_msg = rep.reply_to_message
    elif rep.video or rep.document:
        vid_msg = rep
        if message.audio: aud_msg = message

    if not vid_msg or not aud_msg or not (vid_msg.video or vid_msg.document):
        await message.reply("Could not find both video and audio. Make sure the audio is a reply to the video.")
        return

    task = await queue_manager.add_task(message.from_user.id, message.chat.id, "Add Audio", message)
    m = await message.reply("Processing addaudio...")
    await task.ready_event.wait()

    v_path = os.path.join(DOWNLOAD_DIR, f"v_{task.id}.mp4")
    a_path = os.path.join(DOWNLOAD_DIR, f"a_{task.id}.mp3")
    out = os.path.join(DOWNLOAD_DIR, f"out_{task.id}.mp4")
    try:
        await download_with_progress(client, vid_msg, v_path, message.chat.id, message.from_user.id, status_msg_id=m.id)
        await download_with_progress(client, aud_msg, a_path, message.chat.id, message.from_user.id, status_msg_id=m.id)
        await run_ffmpeg(['-y', '-i', v_path, '-i', a_path, '-map', '0:v', '-map', '1:a', '-c', 'copy', out])
        await client.send_video(message.chat.id, out, reply_to_message_id=vid_msg.id)
    except Exception as e:
        await m.edit(f"Failed: {e}")
    finally:
        for f in [v_path, a_path, out]:
            if os.path.exists(f): os.remove(f)
        queue_manager.remove_task(task.id)
        await m.delete()

@Client.on_message(filters.command("remaudio"))
@authorized_only
async def remaudio_cmd(client: Client, message: Message):
    rep = message.reply_to_message
    if not rep or not (rep.video or rep.document):
        await message.reply("Reply to a video.")
        return

    task = await queue_manager.add_task(message.from_user.id, message.chat.id, "Rem Audio", message)
    m = await message.reply("Removing audio...")
    await task.ready_event.wait()

    path = os.path.join(DOWNLOAD_DIR, f"rem_{task.id}.mp4")
    out = os.path.join(DOWNLOAD_DIR, f"noaudio_{task.id}.mp4")
    try:
        await download_with_progress(client, rep, path, message.chat.id, message.from_user.id, status_msg_id=m.id)
        await run_ffmpeg(['-y', '-i', path, '-an', '-vcodec', 'copy', out])
        await client.send_video(message.chat.id, out, reply_to_message_id=rep.id)
    except Exception as e:
        await m.edit(f"Failed: {e}")
    finally:
        for f in [path, out]:
            if os.path.exists(f): os.remove(f)
        queue_manager.remove_task(task.id)
        await m.delete()
