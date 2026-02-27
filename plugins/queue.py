
from pyrogram import Client, filters
from pyrogram.types import Message
from utils import authorized_only, user_selections
from queue_manager import queue_manager

@Client.on_message(filters.command("status"))
@authorized_only
async def show_status(client: Client, message: Message):
    status_text = []
    chat_id = message.chat.id
    if chat_id in user_selections:
        for uid in user_selections[chat_id]:
            if not isinstance(user_selections[chat_id][uid], dict): continue
            status_text.append(f"User {uid}: {user_selections[chat_id][uid].get('status', 'Idle')}")
    await message.reply("\n".join(status_text) if status_text else "No active processes.")

@Client.on_message(filters.command("list"))
@authorized_only
async def list_queue(client: Client, message: Message):
    await message.reply(queue_manager.get_queue_info())

@Client.on_message(filters.command("cancel"))
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
