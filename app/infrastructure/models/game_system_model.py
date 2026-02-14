#app/infrastructure/models/game_system_model.py
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text

from app.infrastructure.models.base_model import BaseModel

class GameSystemModel(BaseModel):
    """Модель, описывающая игровую систему

    Справочник игровых систем с описанием правил.

    Связи:
        * Один-ко-многим: games (игры на этой системе), characters (персонажи)

    Ключевые поля:
        * name — название системы (уникальное, D&D 5e, GURPS)
        * description — описание правил (Text, nullable)
    """
    __tablename__ = 'game_systems'

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)

    # Связи One-to-Many
    games: Mapped[list["GameModel"]] = relationship(back_populates='game_system') # type: ignore[import]
    characters: Mapped[list["CharacterModel"]] = relationship(back_populates='game_system') # type: ignore[import]