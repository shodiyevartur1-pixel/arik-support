import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import db  # <-- BU YERNI O'ZGARTIRDIM
from handlers import router
from middlewares import AntiSpamMiddleware


# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

async def main():
    # Bot va Dispatcher
    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Ma'lumotlar bazasini tayyorlash
    await db.create_tables()
    
    # Middleware ulash
    dp.message.middleware(AntiSpamMiddleware())
    
    # Router ulash
    dp.include_router(router)
    
    # Botni ishga tushirish
    print("🤖 Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi!")