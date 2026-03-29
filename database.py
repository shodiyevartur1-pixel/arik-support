import aiosqlite
from config import DB_NAME

class Database:
    def __init__(self, db_name):
        self.db_name = db_name

    async def create_tables(self):
        async with aiosqlite.connect(self.db_name) as db:
            # USERS JADVALI
            # DIQQAT: language ga DEFAULT 'uz' qo'ymadik, None bo'ladi
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
            await db.commit()
            print("✅ Ma'lumotlar bazasi tayyor!")

    async def add_user(self, user_id, username, full_name):
        async with aiosqlite.connect(self.db_name) as db:
            # Tilni aniq NULL (None) qilib kiritamizki, so'rashi uchun
            await db.execute('''
                INSERT INTO users (user_id, username, full_name, language, last_activity)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET 
                    username=?, 
                    full_name=?, 
                    last_activity=CURRENT_TIMESTAMP
            ''', (user_id, username, full_name, None, username, full_name))
            await db.commit()

    async def get_user(self, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            return await cursor.fetchone()

    async def set_language(self, user_id, lang):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang, user_id))
            await db.commit()

    async def ban_user(self, user_id, status=1):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('UPDATE users SET is_banned = ? WHERE user_id = ?', (status, user_id))
            await db.commit()

    async def add_message(self, user_id, direction, content_type):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                INSERT INTO messages (user_id, direction, content_type) VALUES (?, ?, ?)
            ''', (user_id, direction, content_type))
            await db.execute('UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?', (user_id,))
            await db.commit()

    async def get_stats(self):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('SELECT COUNT(*) FROM users')
            total_users = (await cursor.fetchone())[0]
            
            cursor = await db.execute('SELECT COUNT(*) FROM messages')
            total_msgs = (await cursor.fetchone())[0]
            
            cursor = await db.execute(
                "SELECT COUNT(*) FROM users WHERE last_activity >= datetime('now', '-1 day')"
            )
            active_users = (await cursor.fetchone())[0]
            
            return total_users, total_msgs, active_users

    async def get_all_users(self):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('SELECT user_id FROM users')
            return [row[0] for row in await cursor.fetchall()]

    async def get_users_count(self):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('SELECT COUNT(*) FROM users')
            return (await cursor.fetchone())[0]

    async def get_users_page(self, limit, offset):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT user_id, full_name, username, is_banned FROM users ORDER BY last_activity DESC LIMIT ? OFFSET ?', 
                (limit, offset)
            )
            return await cursor.fetchall()

    async def count_user_messages(self, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('SELECT COUNT(*) FROM messages WHERE user_id = ?', (user_id,))
            return (await cursor.fetchone())[0]

db = Database(DB_NAME)
