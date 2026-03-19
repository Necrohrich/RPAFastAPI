#app/infrastructure/models/user_model.py
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, BigInteger, Integer, Index
from sqlalchemy import Enum as SQLEnum

from app.domain.enums.platform_role_enum import PlatformRoleEnum
from app.infrastructure.models.base_model import BaseModel

class UserModel(BaseModel):
    """Модель, описывающая пользователя

     Основная сущность платформы. Содержит email, Discord ID, пароль, роль и версию токена.

    Связи:
        * Один-ко-многим: games (автор игр), characters (персонажи), participated_games (игры участия)

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

    # Связи One-to-Many
    games: Mapped[list["GameModel"]] = relationship(back_populates='author') # type: ignore[import]
    characters: Mapped[list["CharacterModel"]] = relationship(back_populates='author') # type: ignore[import]
    participated_games: Mapped[list["GamePlayerModel"]] = relationship(back_populates="user") # type: ignore[import]
    game_reviews: Mapped[list["GameReviewModel"]] = relationship(  # type: ignore[import]
        foreign_keys="[GameReviewModel.user_id]",
        back_populates="user",
    )

    __table_args__ = (
        Index(
            "uq_users_email_global",
            "primary_email",
            "secondary_email",
            unique=True,
        ),
        Index(
            "uq_users_discord_id_global",
            "primary_discord_id",
            "secondary_discord_id",
            unique=True,
        )
    )
