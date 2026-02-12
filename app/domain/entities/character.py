#app/domain/entities/character.py

from dataclasses import dataclass
from uuid import UUID
from app.domain.entities.base_entity import BaseEntity

@dataclass(kw_only=True)
class Character(BaseEntity):
    """
    Domain Entity representing character.

    Attributes:
        name (str): уникальное имя персонажа.
        user_id (UUID): Указывает идентификатор привязанного User.
        game_id (UUID): Указывает идентификатор привязанного Game.
        avatar (str): Ссылка на аватар персонажа.

    Warning:
        - У одной игры не может быть несколько одинаковых имен персонажей.
    """
    name: str
    user_id: UUID
    game_id: UUID
    avatar: str = ""
