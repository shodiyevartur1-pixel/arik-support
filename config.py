import os

# Bot Tokeni - Avval Environment Variable dan oladi, yo'qsa pastdagisini ishlatadi
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8698487561:AAE4lyN_H50tckwj7fZTKNcMO1JOGeM60Ig")

# Admin ID lar (string ko'rinishida kelganda listga aylantiramiz)
admin_ids_str = os.environ.get("ADMIN_ID", "8059999086,7612085208")
ADMIN_ID = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]

# Anti-spam sozlamalari
SPAM_LIMIT = 100000
SPAM_WINDOW = 100000

# Ma'lumotlar bazasi fayli
DB_NAME = "bot_database.db"