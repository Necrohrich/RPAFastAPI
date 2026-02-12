#app/domain/entities/game_system.py

from dataclasses import dataclass
from app.domain.entities.base_entity import BaseEntity

@dataclass(kw_only=True)
class GameSystem(BaseEntity):
    """
    Domain Entity representing a game system.

    Attributes:
        name (str): Короткое название игровой системы.
        description (str): Описание игровой системы.
    """
    name: str
    description: str = ""