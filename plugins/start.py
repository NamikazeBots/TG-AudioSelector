
import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, CallbackQuery
from pyrogram.enums import ChatAction, ParseMode

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

def random_choice(l):
    return random.choice(l)

@Client.on_message(filters.command("start"))
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
        await client.send_photo(chat_id=message.chat.id, photo=START_PIC, caption=caption, reply_markup=create_main_buttons(), parse_mode=ParseMode.HTML)
    else:
        await client.send_message(chat_id=message.chat.id, text=caption, reply_markup=create_main_buttons(), parse_mode=ParseMode.HTML)

@Client.on_callback_query(filters.regex("about"))
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

@Client.on_callback_query(filters.regex("back"))
async def back_cb(client: Client, callback_query: CallbackQuery):
    caption = (
        f"<pre>Hᴇʏᴏ ᴄᴜᴛɪᴇ</pre>\n"
        f"<b><blockquote>›› ɪ’ᴍ ᴀ ʜᴀɴᴅʏ ᴀᴜᴅɪᴏ ꜱᴇʟᴇᴄᴛᴏʀ ʙᴏᴛ ᴍᴀᴅᴇ ᴛᴏ ʜᴇʟᴘ ʏᴏᴜ ᴄʜᴏᴏꜱᴇ ᴏʀ ʀᴇᴍᴏᴠᴇ ᴀᴜᴅɪᴏ ᴛʀᴀᴄᴋꜱ ꜰʀᴏᴍ ʏᴏᴜʀ ᴠɪᴅᴇᴏꜱ!</b></blockquote>\n"
        f"<b><blockquote>◈ <a href='https://t.me/clutch008'>ABHI : ᴡʜᴇʀᴇ ᴀʀɪsᴇ</a></b></blockquote>"
    )
    await callback_query.message.edit_media(media=InputMediaPhoto(media=START_PIC, caption=caption, parse_mode=ParseMode.HTML), reply_markup=create_main_buttons())
    await callback_query.answer()

@Client.on_callback_query(filters.regex("close"))
async def close_cb(client: Client, callback_query: CallbackQuery):
    try: await callback_query.message.delete()
    except: pass
