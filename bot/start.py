# bot/start.py

"""
Handles the /start command and referral system.
Sends media to new users after verifying force-subscription.
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from bot.force_sub import check_force_sub
from bot.media import deliver_media
from database.mongo import db

@Client.on_message(filters.private & filters.command("start"))
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)

    # Save user in DB
    await db.add_user(user_id)

    # Referral check
    if len(args) > 1 and args[1].startswith("ref"):
        referrer_id = args[1][3:]
        if referrer_id.isdigit() and int(referrer_id) != user_id:
            await db.add_referral(int(referrer_id), user_id)

    # Check Force-Sub
    ok, reply_markup = await check_force_sub(client, user_id)
    if not ok:
        return await message.reply(
            "🔐 <b>You must join required channels to continue.</b>",
            reply_markup=reply_markup,
            parse_mode="html"
        )

    # Deliver media
    await deliver_media(client, user_id, message.chat.id)
