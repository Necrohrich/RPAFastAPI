#app/domain/entities/system_character.py

from dataclasses import dataclass, field
from uuid import UUID

from app.domain.entities.character import Character

@dataclass(kw_only=True)
class SystemCharacter(Character):
    """
        Domain Entity representing a system character, extension of character Entity.

        Attributes:
            game_system_key (UUID): Ключ системы для привязки к игровым правилам.
            sheet_data (dict): Хранит логику анкеты игровой системы

        Warning:
            - Привязка персонажа к игре с отличным game_system_key может вызвать конфликт.
        """
    game_system_key: UUID | None = None
    sheet_data: dict = field(default_factory=dict)
