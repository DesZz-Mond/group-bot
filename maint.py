import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = "8031120568:AAEqvTqXdC8dyEYYIlwcLekOdYarVV-gVWI"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- Список адмінів ---
ADMINS = [839046086]  # твоє ID і старости

# --- Тимчасова база даних у пам’яті ---
students = {}  # user_id: {name, surname, lang, elective, eng_group, tasks}
announcements = []

# --- Меню студента ---
student_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Розклад")],
        [KeyboardButton(text="✏️ Домашнє завдання")],
        [KeyboardButton(text="📢 Оголошення")],
        [KeyboardButton(text="⏰ Розклад дзвінків")]
    ],
    resize_keyboard=True
)

# --- Меню адміна ---
admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👥 Список студентів")],
        [KeyboardButton(text="📢 Надіслати оголошення")],
        [KeyboardButton(text="⚙️ Керування функціями")]
    ],
    resize_keyboard=True
)

# --- /start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    if user_id not in students:
        students[user_id] = {"step": "name"}
        await message.answer("Привіт 👋 Я бот групи!\nВведи своє Ім’я та Прізвище:")
    else:
        # якщо адмін
        if user_id in ADMINS:
            await message.answer("Привіт, адміне!", reply_markup=admin_menu)
        else:
            await message.answer("Привіт 👋 Обери дію:", reply_markup=student_menu)

# --- Реєстрація студента ---
@dp.message(F.text & (lambda msg: students.get(msg.from_user.id, {}).get("step") == "name"))
async def reg_name(message: types.Message):
    user_id = message.from_user.id
    students[user_id]["name"] = message.text
    students[user_id]["step"] = "lang"

    langs = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Німецька", callback_data="lang_Німецька")],
        [InlineKeyboardButton(text="Польська", callback_data="lang_Польська")],
        [InlineKeyboardButton(text="Французька", callback_data="lang_Французька")],
        [InlineKeyboardButton(text="Китайська", callback_data="lang_Китайська")],
    ])
    await message.answer("Оберіть другу іноземну мову:", reply_markup=langs)

@dp.callback_query(F.data.startswith("lang_"))
async def reg_lang(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = callback.data.split("_")[1]
    students[user_id]["lang"] = lang
    students[user_id]["step"] = "elective"

    electives = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Економіка країн світу", callback_data="elective_Економіка")],
        [InlineKeyboardButton(text="Мистецтво презентації", callback_data="elective_Презентації")],
    ])
    await callback.message.answer("Оберіть вибірковий предмет:", reply_markup=electives)
    await callback.answer()

@dp.callback_query(F.data.startswith("elective_"))
async def reg_elective(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    elective = callback.data.split("_")[1]
    students[user_id]["elective"] = elective
    students[user_id]["step"] = "eng_group"

    groups = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Маркова/Шматок", callback_data="group_Маркова")],
        [InlineKeyboardButton(text="Мельник/Шматок", callback_data="group_Мельник")],
    ])
    await callback.message.answer("Оберіть групу з англійської:", reply_markup=groups)
    await callback.answer()

@dp.callback_query(F.data.startswith("group_"))
async def reg_group(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    group = callback.data.split("_")[1]
    students[user_id]["eng_group"] = group
    students[user_id]["tasks"] = []
    students[user_id]["step"] = None

    await callback.message.answer("Реєстрація завершена ✅", reply_markup=student_menu)
    await callback.answer()

# --- Розклад дзвінків ---
@dp.message(F.text == "⏰ Розклад дзвінків")
async def bells(message: types.Message):
    text = (
        "⏰ Розклад дзвінків:\n\n"
        "1) 08:30 – 09:45\n"
        "2) 10:00 – 11:15\n"
        "3) 11:30 – 12:45\n"
        "4) 13:00 – 14:15\n"
        "5) 14:30 – 15:45\n"
        "6) 16:00 – 17:15\n"
        "7) 17:30 – 18:45\n"
        "8) 19:00 – 20:15\n"
    )
    await message.answer(text)

# --- Адмін: список студентів ---
@dp.message(F.text == "👥 Список студентів")
async def list_students(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    text = "📋 Список студентів:\n\n"
    for uid, data in students.items():
        text += f"{data.get('name', 'Невідомо')} | {data.get('lang','-')} | {data.get('elective','-')} | {data.get('eng_group','-')}\n"
    await message.answer(text or "Немає зареєстрованих студентів")

# --- Адмін: надсилання оголошень ---
@dp.message(F.text == "📢 Надіслати оголошення")
async def create_announcement(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("Введіть текст оголошення:")
    students[message.from_user.id]["step"] = "announcement"

@dp.message(F.text & (lambda msg: students.get(msg.from_user.id, {}).get("step") == "announcement"))
async def send_announcement(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    ann_text = message.text
    announcements.append(ann_text)

    for uid in students:
        if uid not in ADMINS:
            try:
                await bot.send_message(uid, f"📢 Оголошення:\n\n{ann_text}")
            except:
                pass
    await message.answer("Оголошення розіслано ✅")
    students[message.from_user.id]["step"] = None

# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
