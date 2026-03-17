# app/infrastructure/models/discord_states/guild_discord_settings_model.py
from typing import Optional

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base_model import BaseModel


class GuildDiscordSettingsModel(BaseModel):
    """Модель настроек Discord-сервера (guild).

    Хранит guild-специфичные настройки бота, не привязанные к конкретной игре.

    Ключевые поля:
        * guild_id — ID Discord-сервера (snowflake, уникальный)
        * role_position_anchor_id — ID роли-якоря: бот размещает временные
          игровые роли непосредственно над этой ролью в иерархии сервера.
          Если NULL — роль создаётся без указания позиции.
    """
    __tablename__ = 'guild_discord_settings'

    guild_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, unique=True, index=True
    )
    role_position_anchor_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True
    )