import os
import sqlite3
from contextlib import closing
from datetime import datetime
from zoneinfo import ZoneInfo

DB_PATH = os.getenv("DB_PATH", "database/users.db")
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "10"))
TIMEZONE = ZoneInfo(os.getenv("TZ_NAME", "Europe/Moscow"))

# Результаты списания задачи
OK = "ok"
LIMIT_REACHED = "limit"
NOT_REGISTERED = "not_registered"


def _connect() -> sqlite3.Connection:
    directory = os.path.dirname(DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def _today() -> str:
    """Сегодняшняя дата строкой YYYY-MM-DD — так же, как она лежит в базе."""
    return datetime.now(TIMEZONE).date().isoformat()


def init_db() -> None:
    with closing(_connect()) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                display_name TEXT NOT NULL,
                school_class INTEGER NOT NULL,
                selected_subject TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def init_limits() -> None:
    """Добавляет колонки счётчика, если их нет. Безопасно вызывать при каждом старте."""
    with closing(_connect()) as connection:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}
        if "tasks_today" not in columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN tasks_today INTEGER NOT NULL DEFAULT 0"
            )
        if "last_task_date" not in columns:
            connection.execute("ALTER TABLE users ADD COLUMN last_task_date TEXT")
        connection.commit()


def try_consume_task(telegram_id: int, limit: int = DAILY_LIMIT) -> tuple[str, int]:
    """
    Пытается списать одну задачу.
    Возвращает (статус, сколько_осталось_после_списания).
    Статус: OK / LIMIT_REACHED / NOT_REGISTERED.
    Счётчик обнуляется сам при смене дня — cron не нужен.
    """
    today = _today()
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT tasks_today, last_task_date FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()

        if row is None:
            return NOT_REGISTERED, 0

        # Новый день -> счётчик с нуля
        used = row["tasks_today"] if row["last_task_date"] == today else 0

        if used >= limit:
            return LIMIT_REACHED, 0

        connection.execute(
            "UPDATE users SET tasks_today = ?, last_task_date = ? WHERE telegram_id = ?",
            (used + 1, today, telegram_id),
        )
        connection.commit()
        return OK, limit - (used + 1)


def refund_task(telegram_id: int) -> None:
    """Возвращает списанную задачу, если запрос к ИИ не удался."""
    today = _today()
    with closing(_connect()) as connection:
        connection.execute(
            """
            UPDATE users
            SET tasks_today = MAX(tasks_today - 1, 0)
            WHERE telegram_id = ? AND last_task_date = ?
            """,
            (telegram_id, today),
        )
        connection.commit()


def save_user(
    telegram_id: int,
    username: str | None,
    display_name: str,
    school_class: int,
) -> None:
    with closing(_connect()) as connection:
        connection.execute(
            """
            INSERT INTO users (telegram_id, username, display_name, school_class)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                display_name = excluded.display_name,
                school_class = excluded.school_class,
                updated_at = CURRENT_TIMESTAMP
            """,
            (telegram_id, username, display_name, school_class),
        )
        connection.commit()


def update_subject(telegram_id: int, subject: str) -> None:
    with closing(_connect()) as connection:
        connection.execute(
            """
            UPDATE users
            SET selected_subject = ?, updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
            """,
            (subject, telegram_id),
        )
        connection.commit()
