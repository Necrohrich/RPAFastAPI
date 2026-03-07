#app/dto/__init__.py

__all__=[
    "RegisterRequestDTO",
    "AuthResponseDTO",
    "LoginRequestDTO",
    "RefreshRequestDTO",
    "UserDTO",
    "ChangePasswordDTO",
    "SecondaryEmailDTO",
    "DiscordDTO",
    "CreateGameSystemDTO",
    "UpdateGameSystemDTO",
    "CreateCharacterDTO",
    "UpdateCharacterDTO",
    "CreateGameDTO",
    "UpdateGameDTO"
]

from app.dto.auth_dtos import *
from app.dto.character_dtos import *
from app.dto.game_dtos import *
from app.dto.game_system_dtos import *
