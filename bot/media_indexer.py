# bot/media_indexer.py

"""
Handles indexing of media messages sent to the bot via /setmedia command.
These messages are added to the media pool.
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from config import ADMINS
from database.mongo import db

@Client.on_message(filters.command("setmedia") & filters.user(ADMINS))
async def set_media_command(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply("🔄 Please reply to a media message from the media channel.")

    original = message.reply_to_message
    if not original.photo and not original.video and not original.document and not original.animation:
        return await message.reply("⚠️ Only media (photo, video, document, animation) is allowed.")

    try:
        await db.add_media(original.message_id)
        return await message.reply("✅ Media has been indexed and added to the pool.")
    except Exception as e:
        return await message.reply(f"❌ Failed to add media.\n\n<code>{e}</code>", parse_mode="html")
