import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv('BOT_TOKEN', '')
    gemini_api_key: str = os.getenv('GEMINI_API_KEY', '')
    admin_id: int = int(os.getenv('ADMIN_ID', '0'))
    gemini_model: str = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    database_path: str = os.getenv('DATABASE_PATH', 'bot.db')
    free_daily_limit: int = int(os.getenv('FREE_DAILY_LIMIT', '7'))
settings = Settings()
if not settings.bot_token: raise RuntimeError('BOT_TOKEN отсутствует')
if not settings.gemini_api_key: raise RuntimeError('GEMINI_API_KEY отсутствует')
