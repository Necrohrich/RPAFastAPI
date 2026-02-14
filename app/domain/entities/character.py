#app/domain/entities/character.py

from dataclasses import dataclass, field
from uuid import UUID
from app.domain.entities.base_entity import BaseEntity

@dataclass(kw_only=True)
class Character(BaseEntity):
    """
    Domain Entity representing character.

    Attributes:
        name (str): имя персонажа.
        user_id (UUID): Указывает идентификатор привязанного User.
        game_id (UUID): Указывает идентификатор привязанного Game.
        avatar (str): Ссылка на аватар персонажа.
        game_system_key (UUID): Ключ системы для привязки к игровым правилам.
        sheet_data (dict): Хранит логику анкеты игровой системы
    """
    name: str
    user_id: UUID
    game_id: UUID
    avatar: str = ""
    game_system_key: UUID | None = None
    sheet_data: dict = field(default_factory=dict)
