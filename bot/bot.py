# bot/bot.py

"""
Initializes the Pyrogram Client for the bot.

This loads all plugins from the 'bot/' folder automatically.
"""

from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

Bot = Client(
    name="fsubbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="bot")  # Autoload all plugin files in 'bot/'
)
