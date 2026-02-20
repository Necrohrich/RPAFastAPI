# app/core/config.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from app.utils.files import get_base_dir

# Абсолютный путь до .env
BASE_DIR = Path(get_base_dir())
ENV_PATH = BASE_DIR / ".env"

# Загружаем переменные окружения из .env
if not ENV_PATH.exists():
    raise FileNotFoundError(f".env файл не найден: {ENV_PATH}")
load_dotenv(dotenv_path=ENV_PATH)

class Settings(BaseSettings):
    """
    Конфигурация приложения

    Загружает переменные окружения из файла .env и предоставляет доступ
    к настройкам для JWT-аутентификации и управления сроком действия токенов.

    Ключевые поля:
        * JWT_SECRET — секрет для подписи JWT
        * JWT_ALGORITHM — алгоритм подписи JWT (по умолчанию HS256)
        * ACCESS_TOKEN_EXPIRE_MINUTES — время жизни access-токена в минутах
        * REFRESH_TOKEN_EXPIRE_DAYS — время жизни refresh-токена в днях
    """
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dummy_for_ide")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

settings = Settings()  # подхватывает JWT_SECRET из окружения

