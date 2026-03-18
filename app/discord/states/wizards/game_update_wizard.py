#app/discord/wizards/game_update_wizard.py

from dataclasses import dataclass, field
from typing import Optional, Any
from uuid import UUID


@dataclass
class GameUpdateState:
    game_id: Optional[UUID] = None
    name: Optional[str] = None
    gm_id: Optional[int] = None
    game_system_id: Optional[UUID] = None
    discord_role_id: Optional[int] = None
    discord_main_channel_id: Optional[int] = None
    game_systems: list = field(default_factory=list)
    current_game: Optional[Any] = None