#app/domain/entities/user.py

from dataclasses import dataclass
from uuid import UUID
from app.domain.entities.base_entity import BaseEntity
from app.domain.enums.platform_role_enum import PlatformRoleEnum


@dataclass(kw_only=True)
class User(BaseEntity):
    """
    Domain Entity representing user.

    Attributes:
        primary_email (str): Основной Email пользователя.
        secondary_email (str): Дополнительный Email пользователя.
        password_hash (str): Пароль пользователя.
        primary_discord_id (int): Основной Discord User ID.
        secondary_discord_id (int): Дополнительный Discord User ID.
        platform_role (PlatformRoleEnum): Особые права пользователя.
    """
    primary_email: str = ""
    secondary_email: str = ""
    password_hash: str = ""
    primary_discord_id: int | None = None
    secondary_discord_id: int | None = None
    platform_role: PlatformRoleEnum | None = None



