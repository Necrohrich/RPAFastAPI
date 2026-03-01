#app/domain/entities/user.py

from dataclasses import dataclass
from app.domain.entities.base_entity import BaseEntity
from app.domain.enums.platform_role_enum import PlatformRoleEnum

@dataclass(kw_only=True)
class User(BaseEntity):
    """
    Domain Entity representing user.

    Attributes:
        login (str): Логин пользователя.
        primary_email (str): Основной Email пользователя.
        password_hash (str): Пароль пользователя.
        secondary_email (str): Дополнительный Email пользователя.
        primary_discord_id (int): Основной Discord User ID.
        secondary_discord_id (int): Дополнительный Discord User ID.
        platform_role (PlatformRoleEnum): Особые права пользователя.
        token_version (int): Версия токена пользователя.
    """
    login: str
    primary_email: str
    password_hash: str
    secondary_email: str | None = None
    primary_discord_id: int | None = None
    secondary_discord_id: int | None = None
    platform_role: PlatformRoleEnum | None = None
    token_version: int



