
import os
import time
import psutil
import speedtest
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import DOWNLOAD_DIR
from utils import authorized_only, download_with_progress, safe_telegram_call
from queue_manager import queue_manager

@Client.on_message(filters.command("getid"))
async def get_chat_id(client: Client, message: Message):
    await safe_telegram_call(message.reply, f"Chat ID: {message.chat.id}, Chat Type: {message.chat.type}")

@Client.on_message(filters.command("sysinfo"))
@authorized_only
async def sysinfo_cmd(client: Client, message: Message):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    await message.reply(f"**System Info:**\nCPU: {cpu}%\nRAM: {ram}%\nDisk: {disk}%")

@Client.on_message(filters.command("speedtest"))
@authorized_only
async def speedtest_cmd(client: Client, message: Message):
    m = await message.reply("Running speedtest...")
    def run_speedtest():
        s = speedtest.Speedtest()
        s.get_best_server()
        s.download()
        s.upload()
        return s.results.dict()

    try:
        res = await asyncio.to_thread(run_speedtest)
        await m.edit(f"**Speedtest:**\nDownload: {res['download']/10**6:.2f} Mbps\nUpload: {res['upload']/10**6:.2f} Mbps\nPing: {res['ping']} ms")
    except Exception as e:
        await m.edit(f"Speedtest failed: {e}")

@Client.on_message(filters.command("ping"))
async def ping_cmd(client: Client, message: Message):
    start = time.time()
    m = await message.reply("Pinging...")
    end = time.time()
    await m.edit(f"Pong! Latency: {int((end - start) * 1000)}ms")

@Client.on_message(filters.command("mediainfo"))
@authorized_only
async def mediainfo_cmd(client: Client, message: Message):
    rep = message.reply_to_message
    if not rep or not (rep.video or rep.document):
        await message.reply("Reply to a video.")
        return

    task = await queue_manager.add_task(message.from_user.id, message.chat.id, "MediaInfo", message)
    m = await message.reply("Fetching media info...")
    await task.ready_event.wait()

    if task.cancel_event.is_set():
        queue_manager.remove_task(task.id)
        await m.edit("Task cancelled.")
        return

    path = None
    try:
        path = os.path.join(DOWNLOAD_DIR, f"info_{task.id}_{rep.id}")
        await download_with_progress(client, rep, path, message.chat.id, message.from_user.id, status_msg_id=m.id)
        import json
        process = await asyncio.create_subprocess_exec(
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        info = json.loads(stdout.decode())

        text = "**Media Info:**\n"
        for stream in info.get('streams', []):
            text += f"- {stream.get('codec_type').capitalize()}: {stream.get('codec_name')}\n"
        text += f"- Format: {info.get('format', {}).get('format_long_name')}\n"
        text += f"- Duration: {float(info.get('format', {}).get('duration', 0)):.2f}s"

        await m.edit(text)
    except Exception as e:
        await m.edit(f"Failed: {e}")
    finally:
        if path and os.path.exists(path): os.remove(path)
        queue_manager.remove_task(task.id)
