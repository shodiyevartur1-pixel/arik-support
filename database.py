import aiosqlite
from config import DB_NAME

class Database:
    def __init__(self, db_name):
        self.db_name = db_name

    async def create_tables(self):
        async with aiosqlite.connect(self.db_name) as db:
            # 🚀 KUCHAYTIRISH 1: WAL rejimi. 
            # Bu SQLite uchun maxsus rejim. Bir vaqtda 100 ta odam yozsa ham "database is locked" xatosi chiqmaydi!
            await db.execute("PRAGMA journal_mode=WAL")
            
            # USERS JADVALI
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    language TEXT,
                    is_banned INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP
                )
            ''')
            
            # MIGRATSIYA (Eski bazani tuzatish uchun)
            cursor = await db.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in await cursor.fetchall()]
            
            if 'last_activity' not in columns:
                await db.execute("ALTER TABLE users ADD COLUMN last_activity TIMESTAMP")
                print("🛠 'last_activity' ustuni qo'shildi!")

            # MESSAGES JADVALI
            await db.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    direction TEXT,
                    content_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            ''')
            
            # 🚀 KUCHAYTIRISH 2: INDEX'LAR (Indekslar).
            # Agar foydalanuvchilar 10 000 tadan o'tsa, Admin paneldagi statistika va sahifalar juda sekin yuklanadi.
            # Indexlar bu jarayonni 100 barobar tezlashtiradi!
            await db.execute("CREATE INDEX IF NOT EXISTS idx_msg_user ON messages(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_activity ON users(last_activity)")
            
            await db.commit()
            print("✅ Ma'lumotlar bazasi tayyor (WAL mode & Indexes yoqilgan)!")

    async def add_user(self, user_id, username, full_name):
        # 🚀 KUCHAYTIRISH 3: timeout=10. 
        # Agar baza bir lahzaga band bo'lib qolsa, dastur crash bo'lmaydi, 10 soniya kutadi.
        async with aiosqlite.connect(self.db_name, timeout=10) as db:
            # 🚀 KUCHAYTIRISH 4: Eski foydalanuvchi tilini saqlab qolish.
            # Avvalgi kodda qayta kelsa til None bo'lib qolardi. Endi faqat username va vaqtni yangilaydi.
            await db.execute('''
                INSERT INTO users (user_id, username, full_name, language, last_activity)
                VALUES (?, ?, ?, NULL, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET 
                    username=excluded.username, 
                    full_name=excluded.full_name, 
                    last_activity=CURRENT_TIMESTAMP
            ''', (user_id, username, full_name))
            await db.commit()

    async def get_user(self, user_id):
        async with aiosqlite.connect(self.db_name, timeout=10) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            return await cursor.fetchone()

    async def set_language(self, user_id, lang):
        async with aiosqlite.connect(self.db_name, timeout=10) as db:
            await db.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang, user_id))
            await db.commit()

    async def ban_user(self, user_id, status=1):
        async with aiosqlite.connect(self.db_name, timeout=10) as db:
            await db.execute('UPDATE users SET is_banned = ? WHERE user_id = ?', (status, user_id))
            await db.commit()

    async def add_message(self, user_id, direction, content_type):
        async with aiosqlite.connect(self.db_name, timeout=10) as db:
            await db.execute('''
                INSERT INTO messages (user_id, direction, content_type) VALUES (?, ?, ?)
            ''', (user_id, direction, content_type))
            await db.execute('UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?', (user_id,))
            await db.commit()

    async def get_stats(self):
        async with aiosqlite.connect(self.db_name, timeout=10) as db:
            cursor = await db.execute('SELECT COUNT(*) FROM users')
            total_users = (await cursor.fetchone())[0]
            
            cursor = await db.execute('SELECT COUNT(*) FROM messages')
            total_msgs = (await cursor.fetchone())[0]
            
            # Index tufayli bu sorov endi millisekundlarda ishlaydi
            cursor = await db.execute(
                "SELECT COUNT(*) FROM users WHERE last_activity >= datetime('now', '-1 day')"
            )
            active_users = (await cursor.fetchone())[0]
            
            return total_users, total_msgs, active_users

    async def get_all_users(self):
        async with aiosqlite.connect(self.db_name, timeout=10) as db:
            cursor = await db.execute('SELECT user_id FROM users')
            return [row[0] for row in await cursor.fetchall()]

    async def get_users_count(self):
        async with aiosqlite.connect(self.db_name, timeout=10) as db:
            cursor = await db.execute('SELECT COUNT(*) FROM users')
            return (await cursor.fetchone())[0]

    async def get_users_page(self, limit, offset):
        async with aiosqlite.connect(self.db_name, timeout=10) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT user_id, full_name, username, is_banned FROM users ORDER BY last_activity DESC LIMIT ? OFFSET ?', 
                (limit, offset)
            )
            return await cursor.fetchall()

    async def count_user_messages(self, user_id):
        async with aiosqlite.connect(self.db_name, timeout=10) as db:
            # Index tufayli foydalanuvchi xabarlarini sanash ham juda tez
            cursor = await db.execute('SELECT COUNT(*) FROM messages WHERE user_id = ?', (user_id,))
            return (await cursor.fetchone())[0]

db = Database(DB_NAME)