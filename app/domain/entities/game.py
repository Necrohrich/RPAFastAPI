#app/domain/entities/game.py

from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.base_entity import BaseEntity

@dataclass(kw_only=True)
class Game(BaseEntity):
    """
    Domain Entity representing a game.

    Attributes:
        name (str): Название игры.
        gm_id (int): User ID мастера.
        discord_role_id(int): Привязка для Discord Role по ID
        discord_main_channel_id(int):Привязка Discord Channel для оповещений по ID
        game_system_key (UUID): Ключ системы для привязки к игровым правилам.
    """
    name: str
    gm_id: int | None = None
    discord_role_id: int | None = None
    discord_main_channel_id: int | None = None
    game_system_key: UUID | None = None