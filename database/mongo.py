# database/mongo.py

"""
MongoDB async client and helper methods for:
- user tracking
- referrals
- media pool
- settings
- force-subscription channels
"""

import motor.motor_asyncio
from config import MONGO_URI

class MongoDB:
    def __init__(self):
        self.client = None

    async def connect(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        self.db = self.client.fsubbot
        self.users = self.db.users
        self.settings = self.db.settings
        self.media = self.db.media
        self.refs = self.db.referrals
        self.channels = self.db.fsub_channels

    async def add_user(self, user_id: int):
        await self.users.update_one({"_id": user_id}, {"$setOnInsert": {"_id": user_id}}, upsert=True)

    async def get_all_users(self):
        return self.users.find()

    async def add_referral(self, referrer: int, referred: int):
        exists = await self.refs.find_one({"referred": referred})
        if not exists:
            await self.refs.insert_one({"referrer": referrer, "referred": referred})

    async def get_referral_count(self, user_id: int) -> int:
        return await self.refs.count_documents({"referrer": user_id})

    async def get_available_bonus(self, user_id: int) -> int:
        reward = (await self.get_settings()).get("referral_reward", 1)
        cap = (await self.get_settings()).get("referral_cap", 0)
        count = await self.get_referral_count(user_id)
        bonus = count * reward
        return min(bonus, cap) if cap > 0 else bonus

    async def get_settings(self) -> dict:
        doc = await self.settings.find_one({"_id": 1}) or {}
        return doc

    async def set_setting(self, key: str, value):
        await self.settings.update_one({"_id": 1}, {"$set": {key: value}}, upsert=True)

    async def add_media(self, msg_id: int):
        await self.media.update_one({"_id": msg_id}, {"$setOnInsert": {"_id": msg_id}}, upsert=True)

    async def get_media_pool(self) -> list:
        cursor = self.media.find({}, {"_id": 1})
        return [doc["_id"] async for doc in cursor]

    async def clear_media_pool(self):
        await self.media.delete_many({})

    async def add_channel(self, ch_id: int):
        await self.channels.update_one({"_id": ch_id}, {"$setOnInsert": {"_id": ch_id}}, upsert=True)

    async def del_channel(self, ch_id: int):
        await self.channels.delete_one({"_id": ch_id})

    async def show_channels(self) -> list:
        cursor = self.channels.find()
        return [doc["_id"] async for doc in cursor]

    async def get_force_sub_channels(self) -> list:
        return await self.show_channels()

    async def can_access(self, user_id: int, cooldown_hours: int) -> bool:
        user = await self.users.find_one({"_id": user_id})
        if not user:
            return True
        last = user.get("last_access")
        if not last:
            return True
        import time
        return time.time() - last >= cooldown_hours * 3600

    async def cooldown_remaining(self, user_id: int, cooldown_hours: int) -> str:
        user = await self.users.find_one({"_id": user_id})
        import time
        if not user or not user.get("last_access"):
            return "0 minutes"
        diff = time.time() - user["last_access"]
        remaining = int(cooldown_hours * 3600 - diff)
        mins = max(1, remaining // 60)
        return f"{mins} minute(s)"

    async def set_last_access(self, user_id: int):
        import time
        await self.users.update_one({"_id": user_id}, {"$set": {"last_access": time.time()}})

    async def parse_buttons(self, raw: str):
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        if not raw:
            return None
        rows = []
        for line in raw.strip().split("\n"):
            buttons = []
            for part in line.split(" | "):
                text, url = part.split(" - ", 1)
                buttons.append(InlineKeyboardButton(text.strip(), url=url.strip()))
            rows.append(buttons)
        return InlineKeyboardMarkup(rows)

db = MongoDB()
