# app/dto/character_dtos.py
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class CreateCharacterDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    game_system_id: Optional[UUID] = None
    game_id: Optional[UUID] = None
    avatar: Optional[str] = None
    sheet_data: dict = {}

class UpdateCharacterDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    game_id: Optional[UUID] = None
    avatar: Optional[str] = None
    sheet_data: Optional[dict] = None