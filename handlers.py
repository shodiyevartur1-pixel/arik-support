from aiogram import Router, F, types, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import datetime
import asyncio

from config import ADMIN_ID
from database import db
import keyboards as kb
from filters import IsAdmin

router = Router()

# --- FSM States ---
class Form(StatesGroup):
    waiting_for_message = State()
    waiting_for_broadcast = State()
    waiting_for_broadcast_confirm = State() 
    waiting_for_ban_id = State()
    waiting_for_unban_id = State()
    waiting_for_admin_reply = State()
    waiting_for_search_id = State()

# --- YORDAMCHI FUNKSIYALAR ---

def get_safe_lang(user_data):
    if not user_data:
        return 'uz'
    return user_data['language'] or 'uz'

def safe_date(date_obj):
    if not date_obj: return "Noma'lum"
    return str(date_obj).split('.')[0]

# Admin ID ni doim ro'yxatga aylantiruvchi funksiya
def get_admin_ids():
    if isinstance(ADMIN_ID, (list, tuple)):
        return ADMIN_ID
    return [ADMIN_ID]

# ----------- /START ------------
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    
    try:
        await db.add_user(user.id, user.username, user.full_name)
    except Exception as e:
        print(f"Xatolik (Foydalanuvchi qo'shishda): {e}")
    
    user_data = await db.get_user(user.id)
    
    if user_data and user_data['is_banned'] == 1:
        await message.answer("⛔ Siz bloklangansiz!", reply_markup=types.ReplyKeyboardRemove())
        return

    lang = get_safe_lang(user_data)
    
    if not user_data or not user_data['language']:
        await message.answer(
            "🇺🇿 Assalomu alaykum! Iltimos, tilni tanlang.\n\n"
            "🇷🇺 Здравствуйте! Пожалуйста, выберите язык.",
            reply_markup=kb.language_keyboard())
    else:
        text = (f"Xush kelibsiz, {user.full_name}! 👋\n"
                f"Ushbu bot orqali siz Law adminiga murojaat qilishingiz mumkin.") if lang == 'uz' else \
               (f"Добро пожаловать, {user.full_name}! 👋\n"
                f"Через этого бота вы можете обратиться к Law.")
        await message.answer(text, reply_markup=kb.main_menu_keyboard(lang))

# ----------- Til va Sozlamalar ------------
@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    await db.set_language(callback.from_user.id, lang)
    
    text = (f"✅ Til o'zgartirildi!\n\n"
            f"Xush kelibsiz, {callback.from_user.full_name}! 👋\n"
            f"Ushbu bot orqali siz Law adminiga murojaat qilishingiz mumkin.") if lang == 'uz' else \
           (f"✅ Язык изменен!\n\n"
            f"Добро пожаловать, {callback.from_user.full_name}! 👋\n"
            f"Через этого бота вы можете обратиться к Law.")
    
    try:
        await callback.message.edit_text(text)
    except:
        pass
    
    await callback.message.answer("🏠 Bosh menyu:", reply_markup=kb.main_menu_keyboard(lang))
    await callback.answer()

@router.message(F.text == "⚙️ Sozlamalar")
@router.message(F.text == "⚙️ Настройки")
async def settings(message: types.Message):
    user_data = await db.get_user(message.from_user.id)
    lang = get_safe_lang(user_data)
    text = "⚙️ Sozlamalar bo'limi" if lang == 'uz' else "⚙️ Раздел настроек"
    await message.answer(text, reply_markup=kb.settings_keyboard(lang))

@router.callback_query(F.data == "change_lang")
async def change_language(callback: types.CallbackQuery):
    await callback.message.answer("Tilni tanlang / Выберите язык:", reply_markup=kb.language_keyboard())
    await callback.answer()

# ----------- Bot haqida ------------
@router.message(F.text == "ℹ️ Bot haqida")
@router.message(F.text == "ℹ️ О боте")
async def about_bot(message: types.Message):
    user_data = await db.get_user(message.from_user.id)
    lang = get_safe_lang(user_data)
    text = ("🤖 <b>Bot haqida</b>\n\n"
            "Bu bot orqali siz Law adminiga to'g'ridan-to'g'ri murojaat yo'llashingiz mumkin.\n\n"
            "📦 Versiya: 2.0 (Kuchaytirilgan)\n👨‍💻 Dasturchi: @budjet_uz") if lang == 'uz' else \
           ("🤖 <b>О боте</b>\n\n"
            "Через этого бота вы можете отправить обращение @Budjet_uz.\n\n"
            "📦 Версия: 2.01 (Усиленный)\n👨‍💻 Разработчик: @Budjet_uz")
    await message.answer(text, parse_mode="HTML")

# ----------- Murojaat yuborish ------------
@router.message(F.text == "📩 Murojaat yuborish")
@router.message(F.text == "📩 Отправить обращение")
async def start_contact(message: types.Message, state: FSMContext):
    user_data = await db.get_user(message.from_user.id)
    lang = get_safe_lang(user_data)
    
    if user_data and user_data['is_banned'] == 1:
        await message.answer("⛔ Siz bloklangansiz!", reply_markup=types.ReplyKeyboardRemove())
        return

    text = ("✍️ Law adminiga murojaatingizni yozing.\nRasm, video, ovozli xabar yuborishingiz mumkin.") if lang == 'uz' else \
           ("✍️ Law Напишите ваше обращение.\nВы можете отправить фото, видео или голосовое сообщение.")
    await message.answer(text, reply_markup=kb.cancel_keyboard(lang))
    await state.set_state(Form.waiting_for_message)

@router.message(Form.waiting_for_message)
async def process_message(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    lang = get_safe_lang(user_data)
    
    if message.text in ["❌ Bekor qilish", "❌ Отмена"]:
        await state.clear()
        await message.answer("🏠 Bosh menyu" if lang == 'uz' else "🏠 Главное меню", reply_markup=kb.main_menu_keyboard(lang))
        return

    username = f"@{message.from_user.username}" if message.from_user.username else "Yo'q"
    time_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    
    content_type = "text"
    if message.photo: content_type = "photo"
    elif message.video: content_type = "video"
    elif message.voice: content_type = "voice"
    
    admins = get_admin_ids()
    info_text = (f"👤 <b>Yangi murojaat!</b>\n"
                 f"🆔 ID: <code>{user_id}</code>\n"
                 f"👤 User: {username}\n"
                 f"📅 Vaqt: {time_str}")
    
    success = False
    for admin_id in admins:
        try:
            await message.copy_to(admin_id)
            await bot.send_message(admin_id, info_text, parse_mode="HTML", reply_markup=kb.admin_reply_keyboard(user_id))
            success = True
        except Exception as e:
            print(f"❌ Admin {admin_id} ga yuborib bo'lmadi: {e}")
    
    if success:
        await db.add_message(user_id, "to_admin", content_type)
        confirmation = "✅ Sizning murojaatingiz yuborildi!" if lang == 'uz' else "✅ Ваше обращение отправлено!"
        await message.answer(confirmation, reply_markup=kb.main_menu_keyboard(lang))
    else:
        await message.answer("❌ Xatolik yuz berdi." if lang == 'uz' else "❌ Произошла ошибка.", reply_markup=kb.main_menu_keyboard(lang))
        
    await state.clear()

# ----------- Mening murojaatlarim ------------
@router.message(F.text == "📋 Mening murojaatlarim")
@router.message(F.text == "📋 Мои обращения")
async def my_appeals(message: types.Message):
    user_data = await db.get_user(message.from_user.id)
    lang = get_safe_lang(user_data)
    msg_count = await db.count_user_messages(message.from_user.id)
    text = (f"📊 Sizning statistikangiz:\n📝 Yuborilgan xabarlar: {msg_count} ta") if lang == 'uz' else \
           (f"📊 Ваша статистика:\n📝 Отправленных сообщений: {msg_count}")
    await message.answer(text)

# =============================================
#             ADMIN PANEL
# =============================================

@router.message(Command("admin"), IsAdmin())
async def admin_panel(message: types.Message):
    await message.answer("🔐 <b>Admin Panel (Pro)</b>", parse_mode="HTML", reply_markup=kb.admin_keyboard())

@router.callback_query(F.data == "admin_back", IsAdmin())
async def admin_back(callback: types.CallbackQuery):
    await callback.message.edit_text("🔐 <b>Admin Panel (Pro)</b>", parse_mode="HTML", reply_markup=kb.admin_keyboard())
    await callback.answer()

@router.callback_query(F.data == "admin_stats", IsAdmin())
async def admin_stats(callback: types.CallbackQuery):
    total_users, total_msgs, active_users = await db.get_stats()
    text = (f"📊 <b>Batafsil Statistika</b>\n\n👥 Jami foydalanuvchilar: {total_users}\n🟢 Faol: {active_users}\n📝 Xabarlar: {total_msgs}")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.admin_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("admin_users_"), IsAdmin())
async def admin_users_list(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[2])
    limit = 5
    offset = (page - 1) * limit
    total_users = await db.get_users_count()
    total_pages = (total_users + limit - 1) // limit
    users = await db.get_users_page(limit, offset)
    if not users and page != 1:
        await callback.answer("Boshqa sahifa yo'q!", show_alert=True)
        return
    text = f"👥 <b>Foydalanuvchilar</b> (Sahifa {page}/{total_pages})"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.admin_user_list_keyboard(users, page, total_pages))
    await callback.answer()

@router.callback_query(F.data == "admin_search", IsAdmin())
async def admin_search_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔍 Foydalanuvchi ID sini kiriting:")
    await state.set_state(Form.waiting_for_search_id)
    await callback.answer()

@router.message(Form.waiting_for_search_id, IsAdmin())
async def admin_search_process(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        user_data = await db.get_user(user_id)
        if user_data:
            msg_count = await db.count_user_messages(user_id)
            status = "🚫 Banlangan" if user_data['is_banned'] else "✅ Faol"
            text = (f"👤 <b>Foydalanuvchi topildi:</b>\n\n🆔 ID: <code>{user_data['user_id']}</code>\n👤 Ism: {user_data['full_name']}\n📈 Status: {status}")
            await message.answer(text, parse_mode="HTML", reply_markup=kb.admin_user_profile_keyboard(user_id, user_data['is_banned']))
        else:
            await message.answer("❌ Bunday ID li foydalanuvchi topilmadi.")
    except ValueError:
        await message.answer("❌ ID faqat raqamlardan iborat bo'lishi kerak!")
    await state.clear()

@router.callback_query(F.data.startswith("view_user_"), IsAdmin())
async def admin_view_user(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    user_data = await db.get_user(user_id)
    if not user_data:
        await callback.answer("Foydalanuvchi topilmadi!", show_alert=True)
        return
    status = "🚫 Banlangan" if user_data['is_banned'] else "✅ Faol"
    text = (f"👤 <b>Profil:</b>\n🆔 ID: <code>{user_data['user_id']}</code>\n👤 Ism: {user_data['full_name']}\n📈 Status: {status}")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.admin_user_profile_keyboard(user_id, user_data['is_banned']))
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_ban_"), IsAdmin())
async def admin_toggle_ban(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    user_data = await db.get_user(user_id)
    if not user_data:
        await callback.answer("Xatolik!", show_alert=True)
        return
    new_status = 0 if user_data['is_banned'] == 1 else 1
    await db.ban_user(user_id, new_status)
    status_text = "✅ Bandan olindi" if new_status == 0 else "🚫 Ban qilindi"
    await callback.answer(f"Foydalanuvchi {status_text}!", show_alert=True)
    # Refresh page
    user_data_new = await db.get_user(user_id)
    status = "🚫 Banlangan" if user_data_new['is_banned'] else "✅ Faol"
    text = (f"👤 <b>Profil:</b>\n🆔 ID: <code>{user_data_new['user_id']}</code>\n📈 Status: {status}")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.admin_user_profile_keyboard(user_id, user_data_new['is_banned']))

# --- ADMIN JAVOB BERISH (YANGILANGAN) ---
@router.callback_query(F.data.startswith("reply_"))
async def admin_reply_start(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.data.split("_")[1]
    await state.update_data(target_user=int(user_id))
    await callback.message.answer("✍️ Javobingizni yozing:")
    await state.set_state(Form.waiting_for_admin_reply)
    await callback.answer()

@router.message(Form.waiting_for_admin_reply)
async def admin_reply_send(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target_user = data.get('target_user')
    sender_id = message.from_user.id
    
    try:
        # 1. Foydalanuvchiga yuborish
        await message.copy_to(target_user)
        await db.add_message(target_user, "from_admin", "reply")
        
        # 2. Boshqa adminlarga xabar berish (Suhbat tarixi uchun)
        admins = get_admin_ids()
        for admin_id in admins:
            if admin_id != sender_id: # Javob yozgan admindan tashqari barchaga
                try:
                    # Xabarni adminlarga nusxalash
                    await bot.copy_message(admin_id, message.chat.id, message.message_id)
                    # Qisqacha izoh
                    await bot.send_message(admin_id, f"↩️ Admin ({sender_id}) foydalanuvchi ({target_user}) ga javob berdi.")
                except Exception as e:
                    print(f"Admin {admin_id} ga javob nusxasi yuborilmadi: {e}")

        # 3. Javob bergan adminga tasdiqlash
        await message.answer("✅ Xabar yuborildi!")
        
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
    await state.clear()

# --- BROADCAST ---
@router.callback_query(F.data == "admin_broadcast", IsAdmin())
async def broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📢 Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:")
    await state.set_state(Form.waiting_for_broadcast)
    await callback.answer()

@router.message(Form.waiting_for_broadcast, IsAdmin())
async def broadcast_preview(message: types.Message, state: FSMContext):
    await state.update_data(msg_id=message.message_id, chat_id=message.chat.id)
    text = "📢 <b>Xabar tayyor!</b>\nQuyidagi xabar barchaga yuboriladi. Tasdiqlaysizmi?"
    await message.answer(text, parse_mode="HTML", reply_markup=kb.admin_broadcast_confirm_keyboard())
    await state.set_state(Form.waiting_for_broadcast_confirm)

@router.callback_query(F.data == "confirm_broadcast", IsAdmin())
async def broadcast_send(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    msg_id = data.get('msg_id')
    chat_id = data.get('chat_id')
    
    if not msg_id:
        await callback.answer("Xatolik: Xabar topilmadi!", show_alert=True)
        await state.clear()
        return

    users = await db.get_all_users()
    success = 0
    fail = 0
    
    status_msg = await callback.message.answer(f"🔄 Yuborilmoqda... (0/{len(users)})")
    
    for i, user_id in enumerate(users):
        try:
            await bot.copy_message(user_id, chat_id, msg_id)
            success += 1
        except:
            fail += 1
        
        if i % 10 == 0:
            try:
                await status_msg.edit_text(f"🔄 Yuborilmoqda... ({i}/{len(users)})")
            except: pass
            
    await status_msg.edit_text(f"✅ Yakunlandi!\nMuvaffaqiyatli: {success}\nXatolik: {fail}")
    await state.clear()

@router.callback_query(F.data == "cancel_broadcast", IsAdmin())
async def broadcast_cancel(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Xabar tarqatish bekor qilindi.")
    await state.clear()

# --- BAN MENU ---
@router.callback_query(F.data == "admin_ban_menu", IsAdmin())
async def ban_menu(callback: types.CallbackQuery):
    buttons = [
        [types.InlineKeyboardButton(text="🚫 Ban qilish (ID)", callback_data="admin_ban"),
         types.InlineKeyboardButton(text="✅ Bandan olish (ID)", callback_data="admin_unban")],
        [types.InlineKeyboardButton(text="🔙 Ortga", callback_data="admin_back")]
    ]
    await callback.message.edit_text("🚫 Ban boshqaruvi", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@router.callback_query(F.data == "admin_ban", IsAdmin())
async def ban_input(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🚫 Ban qilinadigan foydalanuvchi ID sini kiriting:")
    await state.set_state(Form.waiting_for_ban_id)
    await callback.answer()

@router.message(Form.waiting_for_ban_id, IsAdmin())
async def ban_process(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await db.ban_user(user_id, 1)
        await message.answer(f"✅ Foydalanuvchi {user_id} ban qilindi!")
    except:
        await message.answer("❌ Xatolik! ID noto'g'ri.")
    await state.clear()

@router.callback_query(F.data == "admin_unban", IsAdmin())
async def unban_input(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✅ Bandan olinadigan foydalanuvchi ID sini kiriting:")
    await state.set_state(Form.waiting_for_unban_id)
    await callback.answer()

@router.message(Form.waiting_for_unban_id, IsAdmin())
async def unban_process(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await db.ban_user(user_id, 0)
        await message.answer(f"✅ Foydalanuvchi {user_id} bandan olindi!")
    except:
        await message.answer("❌ Xatolik! ID noto'g'ri.")
    await state.clear()