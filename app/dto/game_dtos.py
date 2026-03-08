# app/dto/game_dtos.py
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.domain.enums import PlayerStatusEnum
from app.dto.game_system_dtos import GameSystemResponseDTO
from app.dto.auth_dtos import UserDTO

class CreateGameDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    game_system_id: UUID
    gm_id: Optional[int] = None
    discord_role_id: Optional[int] = None
    discord_main_channel_id: Optional[int] = None

class UpdateGameDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    game_system_id: Optional[UUID] = None
    gm_id: Optional[int] = None
    discord_role_id: Optional[int] = None
    discord_main_channel_id: Optional[int] = None

class GameResponseDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str
    author_id: UUID
    gm_id: Optional[int] = None
    discord_role_id: Optional[int] = None
    discord_main_channel_id: Optional[int] = None
    game_system_id: UUID

class GameDetailedResponseDTO(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: UUID
    name: str
    gm_id: Optional[int] = None
    discord_role_id: Optional[int] = None
    discord_main_channel_id: Optional[int] = None
    author: UserDTO
    game_system: GameSystemResponseDTO

class GamePlayerResponseDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    game_id: UUID
    user_id: UUID
    status: PlayerStatusEnum