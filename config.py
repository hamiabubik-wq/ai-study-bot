import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    gemini_api_key: str
    gemini_model: str
    gemini_fallback_model: str | None
    proxy_url: str | None


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
    gemini_fallback_model = (
        os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.1-flash-lite").strip() or None
    )
    proxy_url = os.getenv("PROXY_URL", "").strip() or None

    missing = []
    if not bot_token:
        missing.append("BOT_TOKEN")
    if not gemini_api_key:
        missing.append("GEMINI_API_KEY")

    if missing:
        raise RuntimeError(
            "Не заполнены переменные окружения: " + ", ".join(missing)
        )

    if gemini_fallback_model == gemini_model:
        gemini_fallback_model = None

    return Config(
        bot_token=bot_token,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        gemini_fallback_model=gemini_fallback_model,
        proxy_url=proxy_url,
    )
