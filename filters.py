from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from config import ADMIN_ID

class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        # Foydalanuvchi ID sini aniqlash (Message yoki CallbackQuery)
        if isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            user_id = event.from_user.id
            
        # ADMIN_ID ro'yxat yoki bitta son ekanligini tekshirish
        if isinstance(ADMIN_ID, (list, tuple)):
            return user_id in ADMIN_ID
        return user_id == ADMIN_ID