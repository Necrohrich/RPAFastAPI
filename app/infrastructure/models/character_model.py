#app/infrastructure/models/character_model.py
import uuid
from typing import Optional, Dict

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, UUID, ForeignKey, Index, UniqueConstraint

from app.infrastructure.models.base_model import BaseModel

class CharacterModel(BaseModel):
    """Модель, описывающая персонажа

    Связывает игрока, игру и систему правил с данными листа персонажа.

    Связи:
        * Многие-к-одному: author (User), game (Game), game_system (GameSystem)

    Ключевые поля:
        * name — имя персонажа, уникален для каждой игры (index)
        * user_id/game_id — владелец и игра (FK)
        * sheet_data — JSON данные листа (Dict)
    """
    __tablename__ = 'characters'

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('games.id'),
        nullable=True,
        index=True
    )
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    game_system_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('game_systems.id'),
        nullable=True,
        index=True
    )
    sheet_data: Mapped[Dict[str, int]] = mapped_column(JSON, default=dict)

    #Связи Many-to-One
    author: Mapped["UserModel"] = relationship(back_populates='characters') # type: ignore[import]
    game: Mapped["GameModel"] = relationship(back_populates='characters') # type: ignore[import]
    game_system: Mapped["GameSystemModel"] = relationship(back_populates='characters') # type: ignore[import]

    __table_args__ = (
        UniqueConstraint('name', 'game_id', name='uq_character_name_game'),
        Index('ix_characters_user_game', 'user_id', 'game_id'),
    )