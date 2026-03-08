#app/dto/auth_dtos.py
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, ConfigDict

from app.domain.enums.platform_role_enum import PlatformRoleEnum

class RegisterRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    login: str = Field(min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    discord_id: Optional[int] = None

class AuthResponseDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    device_info: Optional[str] = None

class RefreshRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str
    device_info: Optional[str] = None

class UserDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    login: str
    primary_email: EmailStr
    secondary_email: Optional[EmailStr] = None
    primary_discord_id: Optional[int] = None
    secondary_discord_id: Optional[int] = None
    platform_role: Optional[PlatformRoleEnum] = None

class ChangePasswordDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    old_password: str
    new_password: str

class SecondaryEmailDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr

class DiscordDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    discord_id: int