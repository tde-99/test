# bot/media.py

"""
Handles media delivery logic:
- Sends random media from the database pool
- Applies caption and buttons
- Auto-deletes after a configured delay
"""

import random, asyncio
from pyrogram import Client
from config import MEDIA_CHANNEL
from database.mongo import db

async def deliver_media(client: Client, user_id: int, chat_id: int):
    settings = await db.get_settings()
    cooldown = settings.get("cooldown_hours", 0)
    delete_delay = settings.get("delete_delay", 0)

    # Enforce cooldown
    if not await db.can_access(user_id, cooldown):
        wait = await db.cooldown_remaining(user_id, cooldown)
        return await client.send_message(chat_id, f"⏳ Please wait {wait} before accessing again.")

    count = settings.get("media_count", 1)
    caption = settings.get("caption", "")
    buttons = await db.parse_buttons(settings.get("buttons", ""))
    media_pool = await db.get_media_pool()

    if not media_pool:
        return await client.send_message(chat_id, "⚠️ No media is currently available.")

    selected = random.sample(media_pool, min(len(media_pool), count))
    await db.set_last_access(user_id)

    for msg_id in selected:
        try:
            sent = await client.copy_message(
                chat_id,
                MEDIA_CHANNEL,
                msg_id,
                caption=caption,
                parse_mode="html",
                reply_markup=buttons
            )
            if delete_delay > 0:
                asyncio.create_task(delete_after(client, sent.chat.id, sent.id, delete_delay * 60))
        except:
            continue

    return True

async def delete_after(client: Client, chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id, message_id)
    except:
        pass
