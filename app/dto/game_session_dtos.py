# app/dto/game_session_dtos.py
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.enums import GameSessionStatusEnum


class CreateGameSessionDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    game_id: UUID
    discord_event_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class UpdateGameSessionDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class GameSessionResponseDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    game_id: UUID
    session_number: int
    discord_event_id: Optional[int] = None
    status: Optional[GameSessionStatusEnum] = None
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: Optional[datetime] = None