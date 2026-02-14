#app/infrastructure/models/game_session_model.py
import uuid
from typing import Optional, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, UUID, ForeignKey, Integer, CheckConstraint, BigInteger, DateTime, Index, UniqueConstraint
from sqlalchemy import Enum as SQLEnum

from app.domain.enums.game_session_status_enum import GameSessionStatusEnum
from app.infrastructure.models.base_model import BaseModel

class GameSessionModel(BaseModel):
    """Модель, описывающая игровую сессию

    Сессия с номером, статусом, Discord событием и временными рамками.

    Связи:
        * Многие-к-одному: game (родительская игра)

    Ключевые поля:
        * game_id — игра (FK → games.id)
        * session_number — номер сессии в кампании (int > 0)
        * discord_event_id — Discord событие (уникальное)
        * status — статус (ACTIVE/CANCELED/IGNORED/CREATED/COMPLETED)
        * started_at/ended_at — время проведения
    """
    __tablename__ = 'game_sessions'

    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('games.id'),
        nullable=False,
        index=True
    )
    session_number: Mapped[int] = mapped_column(Integer(), nullable=False)
    discord_event_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    status: Mapped[Optional[GameSessionStatusEnum]] = mapped_column(
        SQLEnum(GameSessionStatusEnum, name="game_session_status_enum")
    )
    title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text(2000), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    started_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Связи Many-to-One
    game: Mapped["GameModel"] = relationship(back_populates='game_sessions') # type: ignore[import]

    __table_args__ = (
        UniqueConstraint(
            'game_id',
            'session_number',
            postgresql_where="status NOT IN ('CANCELED', 'IGNORED') OR status IS NULL",
            name='uq_game_active_session_number'
        ),
        CheckConstraint('session_number > 0', name='positive_session_number'),
        CheckConstraint('ended_at > started_at', name='valid_session_dates'),
        Index(
            'ix_game_sessions_active',
            'game_id',
            'status',
            postgresql_where="status NOT IN ('CANCELED', 'IGNORED') OR status IS NULL"
        ),
    )