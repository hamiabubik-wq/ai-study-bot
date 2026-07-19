from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

def main_keyboard(is_admin=False):
    rows = [
        [KeyboardButton(text='💬 Свободный чат'), KeyboardButton(text='💻 Помощник программиста')],
        [KeyboardButton(text='🖼 Анализ изображения'), KeyboardButton(text='📄 Анализ документа')],
        [KeyboardButton(text='🎙 Голосовой чат'), KeyboardButton(text='🌐 Поиск в интернете')],
        [KeyboardButton(text='📜 История'), KeyboardButton(text='👤 Профиль')],
    ]
    if is_admin: rows.append([KeyboardButton(text='🛠 Админ-панель')])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def cancel_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='❌ Отмена')]], resize_keyboard=True)
