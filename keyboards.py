from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

CLASSES = [f"{number} класс" for number in range(1, 12)]

SUBJECTS = [
    "Математика",
    "Русский язык",
    "Литература",
    "Физика",
    "Химия",
    "Биология",
    "Обществознание",
    "История",
    "Английский язык",
]


def _keyboard(items: list[str], width: int = 2) -> ReplyKeyboardMarkup:
    rows = []
    for index in range(0, len(items), width):
        rows.append(
            [KeyboardButton(text=item) for item in items[index:index + width]]
        )
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def classes_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard(CLASSES, width=3)


def subjects_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard(SUBJECTS, width=2)


def input_type_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard(["🖼 Картинка", "✍️ Текст", "🔄 Сменить предмет"], width=2)


def after_answer_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard(
        ["➕ Ещё вопрос", "📚 Сменить предмет", "🏠 Начать заново"],
        width=2,
    )
