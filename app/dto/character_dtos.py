# app/dto/character_dtos.py
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.dto.game_system_dtos import GameSystemResponseDTO
from app.dto.game_dtos import GameResponseDTO
from app.dto.auth_dtos import UserDTO


class CreateCharacterDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    user_id: UUID
    game_system_id: Optional[UUID] = None
    avatar: Optional[str] = None
    sheet_data: dict = {}

class UpdateCharacterDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: Optional[str] = None
    avatar: Optional[str] = None
    sheet_data: Optional[dict] = None

class CharacterResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    game_system_id: Optional[UUID] = None
    game_id: Optional[UUID] = None
    avatar: Optional[str] = None
    sheet_data: Optional[dict] = None

class CharacterDetailResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    name: str
    avatar: Optional[str] = None
    sheet_data: Optional[dict] = None
    author: UserDTO
    game: Optional[GameResponseDTO] = None
    game_system: Optional[GameSystemResponseDTO] = None