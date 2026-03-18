# app/discord/states/active_characters.py

from uuid import UUID
from dataclasses import dataclass, field

@dataclass
class ActiveCharacterEntry:
    """
    Позволяет хранить активного персонажа. От его лица можно, например, посылать сообщения.
    """
    character_id: UUID
    character_name: str
    avatar_url: str | None

# discord_user_id -> ActiveCharacterEntry
_active: dict[int, ActiveCharacterEntry] = {}

def set_active(discord_id: int, entry: ActiveCharacterEntry) -> None:
    _active[discord_id] = entry

def get_active(discord_id: int) -> ActiveCharacterEntry | None:
    return _active.get(discord_id)

def clear_active(discord_id: int) -> None:
    _active.pop(discord_id, None)