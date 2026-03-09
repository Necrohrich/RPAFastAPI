#app/discord/wizards/character_update_wizard.py

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


@dataclass
class CharacterUpdateState:
    character_id: Optional[UUID] = None
    game_system_id: Optional[UUID] = None
    game_systems: list = field(default_factory=list)
