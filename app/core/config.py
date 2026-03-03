# app/core/config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.utils.files import get_base_dir

# Абсолютный путь до .env
BASE_DIR = Path(get_base_dir())

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
        * DISCORD_TOKEN - ключ для обращения к дискорд-сервису
    """
    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    DISCORD_TOKEN: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()

