import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "users.db"


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
