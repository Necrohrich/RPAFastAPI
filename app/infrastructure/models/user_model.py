#app/infrastructure/models/user_model.py
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, BigInteger, CheckConstraint, Integer
from sqlalchemy import Enum as SQLEnum

from app.domain.enums.platform_role_enum import PlatformRoleEnum
from app.infrastructure.models.base_model import BaseModel

class UserModel(BaseModel):
    """Модель, описывающая пользователя

     Основная сущность платформы. Содержит email, Discord ID, пароль, роль и версию токена.

    Связи:
        * Один-ко-многим: games (автор игр), characters (персонажи)

    Ключевые поля:
        * primary_email — основной email (уникальный, NOT NULL)
        * password_hash — хеш пароля bcrypt (String(255))
        * primary_discord_id — Discord ID (BigInteger, nullable)
        * platform_role — права (ADMIN/MODERATOR/SUPPORT)
    """
    __tablename__ = 'users'

    login: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    primary_email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    secondary_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_discord_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, unique=True, index=True)
    secondary_discord_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, unique=True, index=True)
    platform_role: Mapped[Optional[PlatformRoleEnum]] = mapped_column(
        SQLEnum(PlatformRoleEnum, name="platform_role_enum"), nullable=True
    )

    token_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0, index=True)

    # Связи Many-to-One
    games: Mapped[list["GameModel"]] = relationship(back_populates='author') # type: ignore[import]
    characters: Mapped[list["CharacterModel"]] = relationship(back_populates='author') # type: ignore[import]
