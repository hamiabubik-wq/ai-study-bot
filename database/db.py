import sqlite3
import os
from zoneinfo import ZoneInfo
from datetime import date, datetime
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "database/users.db")
DAILY_LIMIT = 10


def _connect():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_limits() -> None:
    """Добавляет колонки счётчика, если их нет. Безопасно вызывать при каждом старте."""
    conn = _connect()
    try:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(users)")}
        if "tasks_today" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN tasks_today INTEGER NOT NULL DEFAULT 0")
        if "last_task_date" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN last_task_date TEXT")
        conn.commit()
    finally:
        conn.close()


def try_consume_task(user_id: int, limit: int = DAILY_LIMIT) -> tuple[bool, int]:
    """
    Пытается списать одну задачу.
    Возвращает (можно_ли, сколько_осталось_после_списания).
    Счётчик сам обнуляется при смене дня — cron не нужен.
    """
    today = datetime.now(ZoneInfo("Europe/Moscow")).date()
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT tasks_today, last_task_date FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if row is None:
            return False, 0                      # не зарегистрирован

        # новый день -> счётчик с нуля
        used = row["tasks_today"] if row["last_task_date"] == today else 0

        if used >= limit:
            return False, 0

        conn.execute(
            "UPDATE users SET tasks_today = ?, last_task_date = ? WHERE user_id = ?",
            (used + 1, today, user_id),
        )
        conn.commit()
        return True, limit - (used + 1)
    finally:
        conn.close()


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as connection:
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


def save_user(
    telegram_id: int,
    username: str | None,
    display_name: str,
    school_class: int,
) -> None:
    with sqlite3.connect(DB_PATH) as connection:
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
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            UPDATE users
            SET selected_subject = ?, updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
            """,
            (subject, telegram_id),
        )
        connection.commit()
