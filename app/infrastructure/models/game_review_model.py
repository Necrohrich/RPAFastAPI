# app/infrastructure/models/game_review_model.py
import uuid
from typing import Optional

from sqlalchemy import UUID, ForeignKey, UniqueConstraint, Index, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums.review_anonymity_enum import ReviewAnonymityEnum
from app.domain.enums.review_rating_enum import ReviewRatingEnum
from app.domain.enums.review_status_enum import ReviewStatusEnum
from app.infrastructure.models.base_model import BaseModel


class GameReviewModel(BaseModel):
    """Модель игрового отзыва.

    Создаётся автоматически при завершении сессии (COMPLETED) для каждого
    присутствовавшего игрока. Игрок заполняет отзыв и отправляет его.

    Связи:
        * Многие-к-одному: game (Game), session (GameSession), user (User)

    Ключевые поля:
        * game_id / session_id / user_id — обязательные FK
        * status — CREATED / SEND / CANCELED
        * anonymity — PUBLIC / PRIVATE
        * rating — оценка (nullable до отправки)
        * comment — текстовый комментарий
        * best_scenes — JSONB {название: тип_сцены}
        * best_npc — JSONB список имён НИП
        * best_player_id — UUID лучшего игрока (nullable)

    Ограничения:
        * Уникальный отзыв: (session_id, user_id) — один игрок, одна сессия
        * Индексы по game_id, session_id, user_id, status для частых запросов
    """
    __tablename__ = "game_reviews"

    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[ReviewStatusEnum] = mapped_column(
        SQLEnum(ReviewStatusEnum, name="review_status_enum"),
        nullable=False,
        default=ReviewStatusEnum.CREATED,
        index=True,
    )
    anonymity: Mapped[ReviewAnonymityEnum] = mapped_column(
        SQLEnum(ReviewAnonymityEnum, name="review_anonymity_enum"),
        nullable=False,
        default=ReviewAnonymityEnum.PUBLIC,
    )
    rating: Mapped[Optional[ReviewRatingEnum]] = mapped_column(
        SQLEnum(ReviewRatingEnum, name="review_rating_enum"),
        nullable=True,
    )
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # JSONB-поля
    # best_scenes: {"название сцены": "comedy" | "horror" | ...}
    best_scenes: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, default=dict
    )
    # best_npc: ["Имя НИП 1", "Имя НИП 2", ...]
    best_npc: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    best_player_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Связи Many-to-One
    game: Mapped["GameModel"] = relationship(foreign_keys=[game_id])  # type: ignore[name-defined]
    session: Mapped["GameSessionModel"] = relationship(foreign_keys=[session_id])  # type: ignore[name-defined]
    user: Mapped["UserModel"] = relationship(foreign_keys=[user_id], back_populates="game_reviews")  # type: ignore[name-defined]
    best_player: Mapped[Optional["UserModel"]] = relationship(foreign_keys=[best_player_id])  # type: ignore[name-defined]

    __table_args__ = (
        # Один игрок — один отзыв на сессию
        UniqueConstraint("session_id", "user_id", name="uq_game_review_session_user"),
        # Составной индекс для выборки отзывов игры по статусу
        Index("ix_game_reviews_game_status", "game_id", "status"),
        # Составной индекс для выборки отзывов сессии по статусу
        Index("ix_game_reviews_session_status", "session_id", "status"),
    )