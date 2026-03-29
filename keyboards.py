from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def language_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def main_menu_keyboard(lang='uz'):
    if lang == 'uz':
        buttons = [
            [KeyboardButton(text="📩 Murojaat yuborish")],
            [KeyboardButton(text="📋 Mening murojaatlarim"), KeyboardButton(text="ℹ️ Bot haqida")],
            [KeyboardButton(text="⚙️ Sozlamalar")]
        ]
    else:
        buttons = [
            [KeyboardButton(text="📩 Отправить обращение")],
            [KeyboardButton(text="📋 Мои обращения"), KeyboardButton(text="ℹ️ О боте")],
            [KeyboardButton(text="⚙️ Настройки")]
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def settings_keyboard(lang='uz'):
    text = "🌐 Tilni o'zgartirish" if lang == 'uz' else "🌐 Сменить язык"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data="change_lang")]])

# --- ADMIN PANEL ---

def admin_keyboard():
    buttons = [
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users_1"),
         InlineKeyboardButton(text="🔍 ID Qidirish", callback_data="admin_search")],
        [InlineKeyboardButton(text="📢 Xabar tarqatish", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🚫 Ban boshqaruvi", callback_data="admin_ban_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_user_list_keyboard(users, page, total_pages):
    buttons = []
    for u in users:
        status_icon = "🚫" if u['is_banned'] else "👤"
        name = u['full_name'] or "No Name"
        buttons.append([InlineKeyboardButton(text=f"{status_icon} {name} (ID: {u['user_id']})", callback_data=f"view_user_{u['user_id']}")])
    
    # Sahifalash tugmalari
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"admin_users_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"admin_users_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
        
    buttons.append([InlineKeyboardButton(text="🔙 Admin Panel", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_user_profile_keyboard(user_id, is_banned):
    status_btn = "✅ Bandan olish" if is_banned else "🚫 Ban qilish"
    buttons = [
        [InlineKeyboardButton(text="💬 Javob yozish", callback_data=f"reply_{user_id}")],
        [InlineKeyboardButton(text=status_btn, callback_data=f"toggle_ban_{user_id}")],
        [InlineKeyboardButton(text="🔙 Ro'yxatga", callback_data="admin_users_1")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_broadcast_confirm_keyboard():
    buttons = [
        [InlineKeyboardButton(text="✅ Tasdiqlash va yuborish", callback_data="confirm_broadcast")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_reply_keyboard(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Javob berish", callback_data=f"reply_{user_id}")]
    ])

def cancel_keyboard(lang='uz'):
    text = "❌ Bekor qilish" if lang == 'uz' else "❌ Отмена"
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=text)]], resize_keyboard=True)