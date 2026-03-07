# app/dto/game_dtos.py
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

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

class GameResponseDTO(BaseModel):...