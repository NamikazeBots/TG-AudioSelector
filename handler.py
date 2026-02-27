
import os
import shutil
import asyncio
import time
import psutil
import speedtest
import logging
import zipfile
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, CallbackQuery
from pyrogram.enums import ChatType, ChatAction, ParseMode
from config import (
    DOWNLOAD_DIR, OWNER_ID, MAX_FILE_SIZE, PREMIUM_USERS,
    DAILY_LIMIT_FREE, DAILY_LIMIT_PREMIUM, DB_CHANNEL_ID
)
from database import db
from utils import (
    get_audio_tracks, select_audio_tracks, download_with_progress,
    upload_with_progress, create_track_selection_keyboard,
    create_format_selection_keyboard, user_selections, sanitize_filename,
    validate_video_file, generate_thumbnail, check_daily_limit, safe_telegram_call,
    authorized_only, update_status_message, run_ffmpeg
)
from queue_manager import queue_manager

logger = logging.getLogger(__name__)

# Stickers and images
START_PIC = "https://telegra.ph/HgBotz-08-09-5"
ABOUT_PIC = "https://telegra.ph/HgBotz-08-09-6"
stickers = [
    "CAACAgUAAxkBAAEOXBhoCoKZ76jevKX-Vc5v5SZhCeQAAXMAAh4KAALJrhlVZygbxFWWTLw2BA"
]
welcome_text = "<i><blockquote>Wᴇʟᴄᴏᴍᴇ, ʙᴀʙʏ… ɪ’ᴠᴇ ʙᴇᴇɴ ᴄʀᴀᴠɪɴɢ ʏᴏᴜʀ ᴘʀᴇsᴇɴᴄᴇ ғᴇᴇʟs ᴘᴇʀғᴇᴄᴛ ɴᴏᴡ ᴛʜᴀᴛ ʏᴏᴜ’ʀᴇ ʜᴇʀᴇ.</blockquote></i>"

def create_main_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Aʙᴏᴜᴛ", callback_data="about"),
            InlineKeyboardButton("Sᴜᴩᴩᴏʀᴛ", url="https://t.me/clutch008"),
        ],
        [
            InlineKeyboardButton("Dᴇᴠᴇʟᴏᴩᴇʀ", url="https://t.me/clutch008"),
        ],
    ])

def register_handlers(app: Client):
    # --- Start & About ---
    @app.on_message(filters.command("start"))
    async def start_cmd(client: Client, message: Message):
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        msg = await message.reply_text(welcome_text, parse_mode=ParseMode.HTML)
        await asyncio.sleep(0.1)
        await msg.edit_text("<b><i><pre>Sᴛᴀʀᴛɪɴɢ...</pre></i></b>", parse_mode=ParseMode.HTML)
        await asyncio.sleep(0.1)
        await msg.delete()
        await client.send_chat_action(message.chat.id, ChatAction.CHOOSE_STICKER)
        await message.reply_sticker(random_choice(stickers))
        caption = (
            f"<pre>Hᴇʏᴏ ᴄᴜᴛɪᴇ</pre>\n"
            f"<b><blockquote>›› ɪ’ᴍ ᴀ ʜᴀɴᴅʏ ᴀᴜᴅɪᴏ ꜱᴇʟᴇᴄᴛᴏʀ ʙᴏᴛ ᴍᴀᴅᴇ ᴛᴏ ʜᴇʟᴘ ʏᴏᴜ ᴄʜᴏᴏꜱᴇ ᴏʀ ʀᴇᴍᴏᴠᴇ ᴀᴜᴅɪᴏ ᴛʀᴀᴄᴋꜱ ꜰʀᴏᴍ ʏᴏᴜʀ ᴠɪᴅᴇᴏꜱ!</b></blockquote>\n"
            f"<b><blockquote>◈ <a href='https://t.me/clutch008'>ABHI : ᴡʜᴇʀᴇ ᴀʀɪsᴇ</a></b></blockquote>"
        )
        if START_PIC:
            await app.send_photo(chat_id=message.chat.id, photo=START_PIC, caption=caption, reply_markup=create_main_buttons(), parse_mode=ParseMode.HTML)
        else:
            await app.send_message(chat_id=message.chat.id, text=caption, reply_markup=create_main_buttons(), parse_mode=ParseMode.HTML)

    @app.on_callback_query(filters.regex("about"))
    async def about_cb(client: Client, callback_query: CallbackQuery):
        about_caption = (
            "<b><blockquote>Hᴇʏ ᴅᴇᴀʀ ᴍʏ ɴᴀᴍᴇ Iuno</b></blockquote>\n"
            f"<b><blockquote>◈ Oᴡɴᴇʀ : <a href='https://t.me/clutch008'>ᴄʟɪᴄᴋ ʜᴇʀᴇ</a>\n"
            f"◈ Dᴇᴠᴇʟᴏᴩᴇʀ : <a href='https://t.me/clutch008'>ᴄʟɪᴄᴋ ʜᴇʀᴇ</a>\n"
            f"◈ Mᴀɪɴ Cʜᴀɴɴᴇʟ : <a href='https://t.me/+HzquTipfQsA1YWFl'>ᴄʟɪᴄᴋ ʜᴇʀᴇ</a>\n"
            f"◈ Uᴩᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ : <a href='https://t.me/BOTSKINGDOMS'>ᴄʟɪᴄᴋ ʜᴇʀᴇ</a></b></blockquote>"
        )
        await callback_query.message.edit_media(media=InputMediaPhoto(media=ABOUT_PIC, caption=about_caption, parse_mode=ParseMode.HTML), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Bᴀᴄᴋ", callback_data="back"), InlineKeyboardButton("Cʟᴏsᴇ", callback_data="close")]]))
        await callback_query.answer()

    @app.on_callback_query(filters.regex("back"))
    async def back_cb(client: Client, callback_query: CallbackQuery):
        caption = (
            f"<pre>Hᴇʏᴏ ᴄᴜᴛɪᴇ</pre>\n"
            f"<b><blockquote>›› ɪ’ᴍ ᴀ ʜᴀɴᴅʏ ᴀᴜᴅɪᴏ ꜱᴇʟᴇᴄᴛᴏʀ ʙᴏᴛ ᴍᴀᴅᴇ ᴛᴏ ʜᴇʟᴘ ʏᴏᴜ ᴄʜᴏᴏꜱᴇ ᴏʀ ʀᴇᴍᴏᴠᴇ ᴀᴜᴅɪᴏ ᴛʀᴀᴄᴋꜱ ꜰʀᴏᴍ ʏᴏᴜʀ ᴠɪᴅᴇᴏꜱ!</b></blockquote>\n"
            f"<b><blockquote>◈ <a href='https://t.me/clutch008'>ABHI : ᴡʜᴇʀᴇ ᴀʀɪsᴇ</a></b></blockquote>"
        )
        await callback_query.message.edit_media(media=InputMediaPhoto(media=START_PIC, caption=caption, parse_mode=ParseMode.HTML), reply_markup=create_main_buttons())
        await callback_query.answer()

    @app.on_callback_query(filters.regex("close"))
    async def close_cb(client: Client, callback_query: CallbackQuery):
        try: await callback_query.message.delete()
        except: pass

    # --- Utility Commands ---
    @app.on_message(filters.command("getid"))
    async def get_chat_id(client: Client, message: Message):
        await safe_telegram_call(message.reply, f"Chat ID: {message.chat.id}, Chat Type: {message.chat.type}")

    @app.on_message(filters.command("status"))
    @authorized_only
    async def show_status(client: Client, message: Message):
        status_text = []
        for uid in user_selections.get(message.chat.id, {}):
            if not isinstance(user_selections[message.chat.id][uid], dict): continue
            status_text.append(f"User {uid}: {user_selections[message.chat.id][uid].get('status', 'Idle')}")
        await message.reply("\n".join(status_text) if status_text else "No active processes.")

    @app.on_message(filters.command("sysinfo"))
    @authorized_only
    async def sysinfo_cmd(client: Client, message: Message):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        await message.reply(f"**System Info:**\nCPU: {cpu}%\nRAM: {ram}%\nDisk: {disk}%")

    @app.on_message(filters.command("speedtest"))
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

    @app.on_message(filters.command("ping"))
    async def ping_cmd(client: Client, message: Message):
        start = time.time()
        m = await message.reply("Pinging...")
        end = time.time()
        await m.edit(f"Pong! Latency: {int((end - start) * 1000)}ms")

    @app.on_message(filters.command("list"))
    @authorized_only
    async def list_queue(client: Client, message: Message):
        await message.reply(queue_manager.get_queue_info())

    @app.on_message(filters.command("cancel"))
    @authorized_only
    async def cancel_task_cmd(client: Client, message: Message):
        if len(message.command) < 2:
            # Traditional cancel for current user
            chat_id, user_id = message.chat.id, message.from_user.id
            if user_id in user_selections.get(chat_id, {}) and user_selections[chat_id][user_id].get('processing'):
                user_selections[chat_id][user_id]['processing'] = False
                await message.reply("Current task marked for cancellation.")
            else:
                await message.reply("Usage: /cancel <task_id> or no ID to cancel your active session.")
            return

        task_id = message.command[1]
        if queue_manager.cancel_task(task_id):
            await message.reply(f"Task `{task_id}` cancelled.")
        else:
            await message.reply(f"Task `{task_id}` not found.")

    @app.on_message(filters.command("us"))
    @authorized_only
    async def set_user_settings(client: Client, message: Message):
        user_id = message.from_user.id
        args = message.command[1:]
        if not args:
            settings = await db.get_all_user_settings(user_id) if db else user_selections.get(message.chat.id, {}).get(user_id, {})
            await message.reply(f"Settings:\nName: {settings.get('default_name', 'Not set')}\nCaption: {settings.get('default_caption', 'Not set')}")
            return
        if len(args) < 2:
            await message.reply("Usage: /us <name> <caption>")
            return
        name, caption = sanitize_filename(args[0]), args[1]
        if db:
            await db.set_user_setting(user_id, 'default_name', name)
            await db.set_user_setting(user_id, 'default_caption', caption)
        else:
            user_selections.setdefault(message.chat.id, {}).setdefault(user_id, {})['default_name'] = name
            user_selections[message.chat.id][user_id]['default_caption'] = caption
        await message.reply("Settings updated.")

    @app.on_message(filters.command("auth") & filters.user(OWNER_ID))
    async def auth_chat(client: Client, message: Message):
        chat_id = message.chat.id
        if db: await db.add_auth(chat_id)
        await message.reply(f"Chat {chat_id} authorized.")

    @app.on_message(filters.command("unauth") & filters.user(OWNER_ID))
    async def unauth_chat(client: Client, message: Message):
        chat_id = message.chat.id
        if db: await db.remove_auth(chat_id)
        await message.reply(f"Chat {chat_id} unauthorized.")

    # --- Media Processing (Main Video/Doc Handler) ---
    @app.on_message((filters.video | filters.document) & ~filters.command(["extract_audio", "extract_sub", "addaudio", "remaudio", "sub", "hsub", "rsub", "trim", "mediainfo", "Marge"]))
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
            user_selections[chat_id][user_id]['processing'] = True
            user_selections[chat_id][user_id]['status_message_id'] = status_msg.id

            name = message.video.file_name if message.video else message.document.file_name
            if not name: name = f"video_{message.id}.mp4"
            if db:
                settings = await db.get_all_user_settings(user_id)
                if 'default_name' in settings: name = settings['default_name']
                if 'default_caption' in settings: user_selections[chat_id][user_id]['default_caption'] = settings['default_caption']

            path = os.path.join(DOWNLOAD_DIR, f"{user_id}_{task.id}_{sanitize_filename(name)}")
            await download_with_progress(client, message, path, chat_id, user_id)

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
            if os.path.exists(path): os.remove(path)
            queue_manager.remove_task(task.id)

    @app.on_callback_query()
    async def handle_callbacks(client: Client, cq: CallbackQuery):
        chat_id, user_id = cq.message.chat.id, cq.from_user.id
        if user_id not in user_selections.get(chat_id, {}):
            await cq.answer("Session not found.", show_alert=True)
            return

        data = cq.data
        info = user_selections[chat_id][user_id]
        status_msg_id = info.get('status_message_id')

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

    # --- Media Tools ---
    @app.on_message(filters.command("extract_audio"))
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
            await download_with_progress(client, rep, path, message.chat.id, message.from_user.id)
            await run_ffmpeg(['-y', '-i', path, '-vn', '-acodec', 'libmp3lame', out])
            await client.send_audio(message.chat.id, out, reply_to_message_id=rep.id)
        except Exception as e:
            await m.edit(f"Failed: {e}")
        finally:
            for f in [path, out]:
                if os.path.exists(f): os.remove(f)
            queue_manager.remove_task(task.id)
            await m.delete()

    @app.on_message(filters.command("extract_sub"))
    @authorized_only
    async def extract_sub_cmd(client: Client, message: Message):
        rep = message.reply_to_message
        if not rep or not (rep.video or rep.document):
            await message.reply("Reply to a video.")
            return

        task = await queue_manager.add_task(message.from_user.id, message.chat.id, "Extract Sub", message)
        m = await message.reply(f"Extracting subtitles... Task ID: `{task.id}`. Waiting...")
        await task.ready_event.wait()

        path = os.path.join(DOWNLOAD_DIR, f"ext_s_{task.id}_{rep.id}.mp4")
        out = os.path.join(DOWNLOAD_DIR, f"sub_{task.id}_{rep.id}.srt")
        try:
            await download_with_progress(client, rep, path, message.chat.id, message.from_user.id)
            await run_ffmpeg(['-y', '-i', path, '-map', '0:s:0', out])
            await client.send_document(message.chat.id, out, reply_to_message_id=rep.id)
        except Exception as e:
            await m.edit(f"Failed or no subs: {e}")
        finally:
            for f in [path, out]:
                if os.path.exists(f): os.remove(f)
            queue_manager.remove_task(task.id)
            await m.delete()

    @app.on_message(filters.command("mediainfo"))
    @authorized_only
    async def mediainfo_cmd(client: Client, message: Message):
        rep = message.reply_to_message
        if not rep or not (rep.video or rep.document):
            await message.reply("Reply to a video.")
            return

        task = await queue_manager.add_task(message.from_user.id, message.chat.id, "MediaInfo", message)
        m = await message.reply("Fetching media info...")
        await task.ready_event.wait()

        path = os.path.join(DOWNLOAD_DIR, f"info_{task.id}_{rep.id}")
        try:
            await download_with_progress(client, rep, path, message.chat.id, message.from_user.id)
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
            if os.path.exists(path): os.remove(path)
            queue_manager.remove_task(task.id)

    @app.on_message(filters.command("addaudio"))
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
            # Check if there's an audio in the current message or its parent
            if message.audio: aud_msg = message
            # This is a bit limited, usually people reply to video with /addaudio and maybe some magic.
            # Let's support: Reply to audio (which is a reply to video).

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
            await download_with_progress(client, vid_msg, v_path, message.chat.id, message.from_user.id)
            await download_with_progress(client, aud_msg, a_path, message.chat.id, message.from_user.id)
            await run_ffmpeg(['-y', '-i', v_path, '-i', a_path, '-map', '0:v', '-map', '1:a', '-c', 'copy', out])
            await client.send_video(message.chat.id, out, reply_to_message_id=vid_msg.id)
        except Exception as e:
            await m.edit(f"Failed: {e}")
        finally:
            for f in [v_path, a_path, out]:
                if os.path.exists(f): os.remove(f)
            queue_manager.remove_task(task.id)
            await m.delete()

    @app.on_message(filters.command("remaudio"))
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
            await download_with_progress(client, rep, path, message.chat.id, message.from_user.id)
            await run_ffmpeg(['-y', '-i', path, '-an', '-vcodec', 'copy', out])
            await client.send_video(message.chat.id, out, reply_to_message_id=rep.id)
        except Exception as e:
            await m.edit(f"Failed: {e}")
        finally:
            for f in [path, out]:
                if os.path.exists(f): os.remove(f)
            queue_manager.remove_task(task.id)
            await m.delete()

    @app.on_message(filters.command(["sub", "hsub"]))
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

        v_path = os.path.join(DOWNLOAD_DIR, f"v_{task.id}.mp4")
        s_path = os.path.join(DOWNLOAD_DIR, f"s_{task.id}.srt")
        out = os.path.join(DOWNLOAD_DIR, f"out_{task.id}.mp4")
        try:
            await download_with_progress(client, vid_msg, v_path, message.chat.id, message.from_user.id)
            await download_with_progress(client, sub_msg, s_path, message.chat.id, message.from_user.id)
            if is_hard:
                await run_ffmpeg(['-y', '-i', v_path, '-vf', f"subtitles='{s_path}'", '-c:a', 'copy', out])
            else:
                await run_ffmpeg(['-y', '-i', v_path, '-i', s_path, '-c', 'copy', '-c:s', 'mov_text', out])
            await client.send_video(message.chat.id, out, reply_to_message_id=vid_msg.id)
        except Exception as e:
            await m.edit(f"Failed: {e}")
        finally:
            for f in [v_path, s_path, out]:
                if os.path.exists(f): os.remove(f)
            queue_manager.remove_task(task.id)
            await m.delete()

    @app.on_message(filters.command("rsub"))
    @authorized_only
    async def rsub_cmd(client: Client, message: Message):
        rep = message.reply_to_message
        if not rep or not (rep.video or rep.document):
            await message.reply("Reply to a video.")
            return

        task = await queue_manager.add_task(message.from_user.id, message.chat.id, "Rem Sub", message)
        m = await message.reply("Removing subtitles...")
        await task.ready_event.wait()

        path = os.path.join(DOWNLOAD_DIR, f"rs_{task.id}.mp4")
        out = os.path.join(DOWNLOAD_DIR, f"nosub_{task.id}.mp4")
        try:
            await download_with_progress(client, rep, path, message.chat.id, message.from_user.id)
            await run_ffmpeg(['-y', '-i', path, '-sn', '-vcodec', 'copy', '-acodec', 'copy', out])
            await client.send_video(message.chat.id, out, reply_to_message_id=rep.id)
        except Exception as e:
            await m.edit(f"Failed: {e}")
        finally:
            for f in [path, out]:
                if os.path.exists(f): os.remove(f)
            queue_manager.remove_task(task.id)
            await m.delete()

    @app.on_message(filters.command("trim"))
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

        path = os.path.join(DOWNLOAD_DIR, f"tr_{task.id}.mp4")
        out = os.path.join(DOWNLOAD_DIR, f"trimmed_{task.id}.mp4")
        try:
            await download_with_progress(client, rep, path, message.chat.id, message.from_user.id)
            await run_ffmpeg(['-y', '-i', path, '-ss', start_t, '-to', end_t, '-c', 'copy', out])
            await client.send_video(message.chat.id, out, reply_to_message_id=rep.id)
        except Exception as e:
            await m.edit(f"Failed: {e}")
        finally:
            for f in [path, out]:
                if os.path.exists(f): os.remove(f)
            queue_manager.remove_task(task.id)
            await m.delete()

    @app.on_message(filters.command("Marge"))
    @authorized_only
    async def merge_cmd(client: Client, message: Message):
        chat_id, user_id = message.chat.id, message.from_user.id

        # Check if user wants to add a file to merge list
        if message.reply_to_message and (message.reply_to_message.video or message.reply_to_message.document):
            user_selections[chat_id].setdefault(user_id, {}).setdefault('merge_files', []).append(message.reply_to_message)
            await message.reply(f"Added to merge list. Current count: {len(user_selections[chat_id][user_id]['merge_files'])}. Use `/Marge now` to start merging.")
            return

        # Check if user wants to start merging
        if len(message.command) > 1 and message.command[1] == "now":
            files_to_merge = user_selections.get(chat_id, {}).get(user_id, {}).get('merge_files', [])
            if len(files_to_merge) < 2:
                await message.reply("Need at least 2 files to merge.")
                return
        else:
            await message.reply("Reply to a video with `/Marge` to add it to the list, then use `/Marge now` to merge them.")
            return

        task = await queue_manager.add_task(user_id, chat_id, "Merge", message)
        m = await message.reply(f"Merging {len(files_to_merge)} files...")
        await task.ready_event.wait()

        paths = []
        try:
            for i, f_msg in enumerate(files_to_merge):
                p = os.path.join(DOWNLOAD_DIR, f"m_{task.id}_{i}.mp4")
                await download_with_progress(client, f_msg, p, chat_id, user_id)
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
                if os.path.exists(f): os.remove(f)
            if user_id in user_selections.get(chat_id, {}) and 'merge_files' in user_selections[chat_id][user_id]:
                user_selections[chat_id][user_id]['merge_files'] = []
            queue_manager.remove_task(task.id)
            await m.delete()

def random_choice(l):
    import random
    return random.choice(l)
