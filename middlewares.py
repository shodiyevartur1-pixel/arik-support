from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from collections import defaultdict
import time
from config import SPAM_LIMIT, SPAM_WINDOW, ADMIN_ID

class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self):
        self.user_timestamps = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        
        # Admin uchun cheklov yo'q
        if user_id == ADMIN_ID:
            return await handler(event, data)

        current_time = time.time()
        timestamps = self.user_timestamps[user_id]
        
        # Eski vaqtlarni tozalash
        self.user_timestamps[user_id] = [t for t in timestamps if current_time - t < SPAM_WINDOW]
        
        # Tekshirish
        if len(self.user_timestamps[user_id]) >= SPAM_LIMIT:
            # Spam aniqlandi
            await event.answer("⚠️ Juda ko'p xabar yubormang! Iltimos, biroz kuting.")
            return None
        
        self.user_timestamps[user_id].append(current_time)
        return await handler(event, data)