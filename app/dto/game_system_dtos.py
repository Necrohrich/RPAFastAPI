# app/dto/game_system_dtos.py
from typing import Optional
from pydantic import BaseModel, ConfigDict

class CreateGameSystemDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: Optional[str] = None

class UpdateGameSystemDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    description: Optional[str] = None