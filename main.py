import asyncio
import logging
import os
import sys
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Fayllaringizdan importlar
try:
    from config import BOT_TOKEN
    from database import db
    from handlers import router
    from middlewares import AntiSpamMiddleware
except ImportError as e:
    print(f"❌ Import xatosi: {e}. Fayllar nomini tekshiring!")
    sys.exit(1)

# --- RENDER UCHUN KICHIK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is active and running!"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    # Render avtomatik beradigan PORTni olish
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
# ---------------------------------

# Loggingni chiroyli ko'rinishga keltiramiz
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def main():
    if not BOT_TOKEN:
        logging.error("❌ BOT_TOKEN topilmadi! Environment Variables'ni tekshiring.")
        return

    # Bot va Dispatcher
    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Ma'lumotlar bazasini tayyorlash
    try:
        await db.create_tables()
        logging.info("✅ Ma'lumotlar bazasi tayyor!")
    except Exception as e:
        logging.error(f"❌ Bazada xatolik: {e}")
    
    # Middleware va Routerlar
    dp.message.middleware(AntiSpamMiddleware())
    dp.include_router(router)
    
    # Botni ishga tushirish (polling)
    logging.info("🤖 Bot polling rejimida ishga tushdi!")
    
    try:
        # Eski xabarlarni o'chirib tashlash (bot o'chiq turganda kelgan xabarlar yopirilib kelmasligi uchun)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    # Flaskni alohida oqimda (thread) ishga tushiramiz
    server_thread = Thread(target=run_flask, daemon=True)
    server_thread.start()
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Terminating bot...")