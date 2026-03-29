from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from collections import defaultdict
import time
from config import SPAM_LIMIT, SPAM_WINDOW, ADMIN_ID

class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.user_timestamps = defaultdict(list)
        # YANGI: Foydalanuvchini vaqtincha "o'chirib qo'yish" (Mute) uchun yangi lug'at
        self.muted_until = defaultdict(float)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        
        # 1. Admin uchun hech qanday cheklov yo'q
        if user_id == ADMIN_ID:
            return await handler(event, data)

        # 2. /start buyrug'i doimo ishlashi kerak (blokdan chiqish uchun)
        if event.text and event.text.startswith('/start'):
            # Agar foydalanuvchi start bosgan bo'lsa, uning barcha eski xatolarini avvalgi holatdan tozalaymiz
            self.user_timestamps[user_id].clear()
            if user_id in self.muted_until:
                del self.muted_until[user_id]
            return await handler(event, data)

        current_time = time.time()

        # 3. MUTED (Jazo) holatini tekshirish
        if user_id in self.muted_until:
            if current_time < self.muted_until[user_id]:
                # Foydalanuvchi hali jazoda. Xabarini jimgina o'chiramiz (botni spamdan asraydi)
                try:
                    await event.delete()
                except:
                    pass
                return None # Bot hech narsa qilmaydi, xato ham bermaydi
            else:
                # Jazo vaqti tugadi! Barcha cheklovlarni oladi
                del self.muted_until[user_id]
                self.user_timestamps[user_id].clear()

        # 4. Eski vaqtlarni tozalash (oynani siljitish)
        self.user_timestamps[user_id] = [
            t for t in self.user_timestamps[user_id] 
            if current_time - t < SPAM_WINDOW
        ]
        
        # 5. Spam limitini tekshirish
        if len(self.user_timestamps[user_id]) >= SPAM_LIMIT:
            # Spam aniqlandi! Foydalanuvchiga 1 marta xabar beramiz va 10 soniyaga bloklaymiz
            self.muted_until[user_id] = current_time + 10.0 # 10 soniyaliq jazo
            
            try:
                await event.answer("⚠️ <b>Spam aniqlandi!</b>\nSiz 10 soniyaga bloklandingiz. Iltimos, kuting.", parse_mode="HTML")
                # Spammer xabarini o'chiramiz
                await event.delete()
            except:
                pass
            return None
        
        # 6. Agar hamma narsa normal bo'lsa, xabarni qayta ishlaymiz
        self.user_timestamps[user_id].append(current_time)
        return await handler(event, data)