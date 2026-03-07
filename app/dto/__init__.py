#app/dto/__init__.py

__all__=[
    "PaginatedResponseDTO",
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
    "GameSystemResponseDTO",
    "CreateCharacterDTO",
    "UpdateCharacterDTO",
    "CreateGameDTO",
    "UpdateGameDTO"
]

from app.dto.auth_dtos import *
from app.dto.character_dtos import *
from app.dto.common_dtos import PaginatedResponseDTO
from app.dto.game_dtos import *
from app.dto.game_system_dtos import *
