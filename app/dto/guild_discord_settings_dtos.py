# app/dto/guild_discord_settings_dtos.py
from typing import Optional
from pydantic import BaseModel, ConfigDict


class GuildSettingsResponseDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    guild_id: int
    role_position_anchor_id: Optional[int] = None