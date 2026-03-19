#app/dto/__init__.py

__all__=[
    # Auth and User
    "PaginatedResponseDTO",
    "RegisterRequestDTO",
    "AuthResponseDTO",
    "LoginRequestDTO",
    "RefreshRequestDTO",
    "UserDTO",
    "ChangePasswordDTO",
    "SecondaryEmailDTO",
    "DiscordDTO",

    # Game System
    "CreateGameSystemDTO",
    "UpdateGameSystemDTO",
    "GameSystemResponseDTO",

    # Character
    "CreateCharacterDTO",
    "UpdateCharacterDTO",
    "CharacterResponseDTO",
    "CharacterDetailResponseDTO",

    # Game
    "CreateGameDTO",
    "UpdateGameDTO",
    "GameResponseDTO",
    "GameDetailedResponseDTO",
    "GamePlayerResponseDTO",

    # Game Session
    "CreateGameSessionDTO",
    "UpdateGameSessionDTO",
    "GameSessionResponseDTO",

    # Discord
    "GuildSettingsResponseDTO",

    # Game Review
    "CreateGameReviewDTO",
    "UpdateGameReviewDTO",
    "SendGameReviewDTO",
    "GameReviewResponseDTO",
    "GameReviewRatingStatsDTO",
    "GameReviewStatsDTO",
    "NpcStatDTO",
    "SceneStatDTO",
    "PlayerStatDTO",
]

from app.dto.auth_dtos import DiscordDTO, SecondaryEmailDTO, ChangePasswordDTO, RefreshRequestDTO, LoginRequestDTO, \
    AuthResponseDTO, RegisterRequestDTO, UserDTO
from app.dto.character_dtos import UpdateCharacterDTO, CreateCharacterDTO, CharacterResponseDTO, \
    CharacterDetailResponseDTO

from app.dto.common_dtos import PaginatedResponseDTO
from app.dto.game_dtos import UpdateGameDTO, CreateGameDTO, GameResponseDTO, GameDetailedResponseDTO, \
    GamePlayerResponseDTO
from app.dto.game_review_dtos import (
    CreateGameReviewDTO,
    UpdateGameReviewDTO,
    SendGameReviewDTO,
    GameReviewResponseDTO,
    GameReviewRatingStatsDTO,
    GameReviewStatsDTO,
    NpcStatDTO,
    SceneStatDTO,
    PlayerStatDTO,
)
from app.dto.game_session_dtos import GameSessionResponseDTO, UpdateGameSessionDTO, CreateGameSessionDTO
from app.dto.game_system_dtos import GameSystemResponseDTO, UpdateGameSystemDTO, CreateGameSystemDTO
from app.dto.guild_discord_settings_dtos import GuildSettingsResponseDTO