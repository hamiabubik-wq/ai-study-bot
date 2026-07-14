import asyncio
import html
import io
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from config import load_config
from database import init_db, save_user, update_subject
from database.db import (
    DAILY_LIMIT,
    LIMIT_REACHED,
    NOT_REGISTERED,
    OK,
    init_limits,
    refund_task,
    try_consume_task,
)
from keyboards import (
    CLASSES,
    SUBJECTS,
    after_answer_keyboard,
    classes_keyboard,
    input_type_keyboard,
    subjects_keyboard,
)
from services import StudyAI
from states import StudyForm

router = Router()
config = load_config()

# Жёсткий потолок ожидания ответа ИИ. Должен быть чуть больше,
# чем таймаут внутри StudyAI, чтобы сработал сначала он.
AI_TIMEOUT_SECONDS = 120

study_ai = StudyAI(
    config.gemini_api_key,
    config.gemini_model,
    proxy_url=config.proxy_url,
    timeout_seconds=AI_TIMEOUT_SECONDS - 10,
)
MAX_TELEGRAM_MESSAGE = 4000


async def send_long_message(message: Message, text: str) -> None:
    text = text.strip()
    if not text:
        await message.answer("Ответ получился пустым. Попробуй переформулировать задание.")
        return

    while text:
        if len(text) <= MAX_TELEGRAM_MESSAGE:
            await message.answer(text)
            break

        split_at = text.rfind("\n", 0, MAX_TELEGRAM_MESSAGE)
        if split_at < 1000:
            split_at = MAX_TELEGRAM_MESSAGE

        chunk = text[:split_at].strip()
        if chunk:
            await message.answer(chunk)
        text = text[split_at:].strip()


async def check_limit(message: Message) -> bool:
    """Списывает одну задачу. Возвращает True, если можно продолжать."""
    try:
        status, left = try_consume_task(message.from_user.id)
    except Exception as error:
        logging.exception("Не удалось проверить лимит: %s", error)
        # Лучше пропустить пользователя, чем сломать бота из-за счётчика
        return True

    if status == NOT_REGISTERED:
        await message.answer("Ты ещё не зарегистрирован. Нажми /start, чтобы начать.")
        return False

    if status == LIMIT_REACHED:
        await message.answer(
            f"На сегодня лимит исчерпан ({DAILY_LIMIT} задач в день).\n"
            "Счётчик обнулится завтра — приходи ещё 🙂"
        )
        return False

    logging.info("Пользователь %s: осталось задач сегодня %s", message.from_user.id, left)
    return True


async def start_registration(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(StudyForm.choosing_class)
    await message.answer(
        "Привет! Я AI-помощник для учёбы.\n\n"
        "Сначала выбери свой класс:",
        reply_markup=classes_keyboard(),
    )


@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await start_registration(message, state)


@router.message(Command("menu"))
async def command_menu(message: Message, state: FSMContext) -> None:
    await start_registration(message, state)


@router.message(F.text == "🏠 Начать заново")
async def restart_button(message: Message, state: FSMContext) -> None:
    await start_registration(message, state)


@router.message(StudyForm.choosing_class, F.text.in_(CLASSES))
async def class_selected(message: Message, state: FSMContext) -> None:
    school_class = int(message.text.split()[0])
    await state.update_data(school_class=school_class)
    await state.set_state(StudyForm.entering_name)
    await message.answer(
        "Как бы вы хотели, чтобы я к вам обращался?",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(StudyForm.choosing_class)
async def invalid_class(message: Message) -> None:
    await message.answer("Пожалуйста, выбери класс кнопкой ниже.")


@router.message(StudyForm.entering_name, F.text)
async def name_entered(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not 2 <= len(name) <= 30:
        await message.answer("Введи имя длиной от 2 до 30 символов.")
        return

    data = await state.update_data(display_name=name)
    save_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        display_name=name,
        school_class=data["school_class"],
    )

    await state.set_state(StudyForm.choosing_subject)
    await message.answer(
        f"Хорошо, {html.escape(name)}! Теперь выбери предмет, по которому нужна помощь:",
        reply_markup=subjects_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@router.message(StudyForm.entering_name)
async def invalid_name(message: Message) -> None:
    await message.answer("Отправь имя обычным текстовым сообщением.")


@router.message(F.text.in_(["📚 Сменить предмет", "🔄 Сменить предмет"]))
async def change_subject(message: Message, state: FSMContext) -> None:
    await state.set_state(StudyForm.choosing_subject)
    await message.answer("Выбери новый предмет:", reply_markup=subjects_keyboard())


@router.message(StudyForm.choosing_subject, F.text.in_(SUBJECTS))
async def subject_selected(message: Message, state: FSMContext) -> None:
    subject = message.text
    await state.update_data(subject=subject)
    update_subject(message.from_user.id, subject)
    await state.set_state(StudyForm.choosing_input_type)
    await message.answer(
        f"Предмет: {subject}.\nКак ты хочешь отправить задание?",
        reply_markup=input_type_keyboard(),
    )


@router.message(StudyForm.choosing_subject)
async def invalid_subject(message: Message) -> None:
    await message.answer("Выбери предмет с помощью кнопок.")


@router.message(StudyForm.choosing_input_type, F.text == "✍️ Текст")
async def text_mode_selected(message: Message, state: FSMContext) -> None:
    await state.set_state(StudyForm.waiting_for_text)
    await message.answer(
        "Пришли условие задачи одним текстовым сообщением.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(StudyForm.choosing_input_type, F.text == "🖼 Картинка")
async def image_mode_selected(message: Message, state: FSMContext) -> None:
    await state.set_state(StudyForm.waiting_for_image)
    await message.answer(
        "Пришли чёткую фотографию задания. Постарайся, чтобы весь текст попал в кадр.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(F.text == "➕ Ещё вопрос")
async def another_question(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("subject"):
        await state.set_state(StudyForm.choosing_subject)
        await message.answer("Сначала выбери предмет:", reply_markup=subjects_keyboard())
        return

    await state.set_state(StudyForm.choosing_input_type)
    await message.answer(
        f"Предмет остаётся: {data['subject']}. Как отправишь следующее задание?",
        reply_markup=input_type_keyboard(),
    )


@router.message(StudyForm.waiting_for_text, F.text)
async def solve_text_task(message: Message, state: FSMContext, bot: Bot) -> None:
    task = message.text.strip()
    if len(task) < 3:
        await message.answer("Условие слишком короткое. Пришли задачу полностью.")
        return

    data = await state.get_data()
    if not data.get("school_class") or not data.get("subject"):
        await message.answer("Что-то сбилось. Нажми /start и выбери класс и предмет заново.")
        return

    if not await check_limit(message):
        return

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    waiting = await message.answer("Разбираю задачу и готовлю подробное решение…")

    try:
        answer = await asyncio.wait_for(
            asyncio.to_thread(
                study_ai.solve_text,
                data["school_class"],
                data["subject"],
                task,
            ),
            timeout=AI_TIMEOUT_SECONDS,
        )
        await waiting.delete()
        await send_long_message(message, answer)
        await message.answer(
            "Готово. Что делаем дальше?",
            reply_markup=after_answer_keyboard(),
        )
    except asyncio.TimeoutError:
        logging.error("Gemini text request timed out after %ss", AI_TIMEOUT_SECONDS)
        refund_task(message.from_user.id)
        await waiting.edit_text(
            "Gemini не ответил за отведённое время. Попробуй ещё раз или упрости задание."
        )
    except Exception as error:
        logging.exception("Gemini text request failed: %s", error)
        refund_task(message.from_user.id)
        await waiting.edit_text(
            f"Не удалось получить ответ от Gemini.\n\nТехническая причина: "
            f"{type(error).__name__}: {str(error)[:300]}"
        )


@router.message(StudyForm.waiting_for_text)
async def text_expected(message: Message) -> None:
    await message.answer("Сейчас я жду условие задачи именно текстом.")


async def _download_image(message: Message, bot: Bot) -> tuple[bytes, str] | None:
    if message.photo:
        telegram_file = await bot.get_file(message.photo[-1].file_id)
        buffer = io.BytesIO()
        await bot.download_file(telegram_file.file_path, destination=buffer)
        return buffer.getvalue(), "image/jpeg"

    if message.document and message.document.mime_type:
        if not message.document.mime_type.startswith("image/"):
            return None
        telegram_file = await bot.get_file(message.document.file_id)
        buffer = io.BytesIO()
        await bot.download_file(telegram_file.file_path, destination=buffer)
        return buffer.getvalue(), message.document.mime_type

    return None


@router.message(StudyForm.waiting_for_image, F.photo | F.document)
async def solve_image_task(message: Message, state: FSMContext, bot: Bot) -> None:
    downloaded = await _download_image(message, bot)
    if downloaded is None:
        await message.answer("Это не изображение. Пришли фотографию задания.")
        return

    image_bytes, mime_type = downloaded
    data = await state.get_data()
    if not data.get("school_class") or not data.get("subject"):
        await message.answer("Что-то сбилось. Нажми /start и выбери класс и предмет заново.")
        return

    if not await check_limit(message):
        return

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    waiting = await message.answer("Изучаю фотографию и готовлю подробное решение…")

    try:
        answer = await asyncio.wait_for(
            asyncio.to_thread(
                study_ai.solve_image,
                data["school_class"],
                data["subject"],
                image_bytes,
                mime_type,
            ),
            timeout=AI_TIMEOUT_SECONDS,
        )
        await waiting.delete()
        await send_long_message(message, answer)
        await message.answer(
            "Готово. Что делаем дальше?",
            reply_markup=after_answer_keyboard(),
        )
    except asyncio.TimeoutError:
        logging.error("Gemini image request timed out after %ss", AI_TIMEOUT_SECONDS)
        refund_task(message.from_user.id)
        await waiting.edit_text(
            "Gemini не ответил за отведённое время. Попробуй ещё раз или пришли фото поменьше."
        )
    except Exception as error:
        logging.exception("Gemini image request failed: %s", error)
        refund_task(message.from_user.id)
        await waiting.edit_text(
            f"Не удалось обработать фотографию.\n\nТехническая причина: "
            f"{type(error).__name__}: {str(error)[:300]}"
        )


@router.message(StudyForm.waiting_for_image)
async def image_expected(message: Message) -> None:
    await message.answer("Сейчас я жду фотографию задания, а не текст.")


@router.message()
async def fallback(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нажми /start, чтобы начать работу с ботом.")
    else:
        await message.answer("Используй кнопки или выполни действие, которое бот попросил выше.")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    init_db()
    init_limits()

    session = AiohttpSession(proxy=config.proxy_url) if config.proxy_url else None
    if config.proxy_url:
        logging.info("Telegram и Gemini: используется прокси %s", config.proxy_url)

    bot = Bot(token=config.bot_token, session=session)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот запущен. Модель: %s", config.gemini_model)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
