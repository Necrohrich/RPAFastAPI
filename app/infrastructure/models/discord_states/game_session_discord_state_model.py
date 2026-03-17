# app/infrastructure/models/discord_states/game_session_discord_state_model.py
import uuid
from typing import Optional

from sqlalchemy import UUID, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base_model import BaseModel


class GameSessionDiscordStateModel(BaseModel):
    """Модель Discord-состояния игровой сессии.

    Хранит Discord-специфичные данные активной сессии, которые не относятся
    к доменной модели и не нужны сайту.

    Создаётся в момент старта сессии (ACTIVE):
        - Через Discord: после завершения View выбора игроков
        - Через сайт: сразу при переходе в ACTIVE, attending_user_ids
          подтягиваются из принятых игроков игры

    Связи:
        * Один-к-одному: session (GameSession)

    Ключевые поля:
        * session_id — сессия (FK → game_sessions.id, unique)
        * attendance_message_id — ID сообщения с View выбора игроков
        * temp_role_id — ID временной Discord роли выданной на сессию
        * attending_user_ids — JSON-массив Discord ID присутствующих игроков
    """
    __tablename__ = 'game_session_discord_states'

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('game_sessions.id', ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    attendance_message_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True
    )
    temp_role_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True
    )
    # Discord User ID присутствующих игроков (snowflake = BigInteger)
    attending_user_ids: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, default=list
    )

    # Связи One-to-One
    session: Mapped["GameSessionModel"] = relationship(  # type: ignore[name-defined]
        back_populates='discord_state'
    )