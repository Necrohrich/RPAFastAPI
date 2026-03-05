#app/dto/auth_dtos.py
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr

from app.domain.enums.platform_role_enum import PlatformRoleEnum

class RegisterRequestDTO(BaseModel):
    login: str = Field(min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    discord_id: int | None

class AuthResponseDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginRequestDTO(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    device_info: str | None = None

class RefreshRequestDTO(BaseModel):
    refresh_token: str
    device_info: str | None = None

class UserDTO(BaseModel):
    id: UUID
    login: str
    primary_email: EmailStr
    secondary_email: EmailStr | None = None
    primary_discord_id: int | None = None
    secondary_discord_id: int | None = None
    platform_role: PlatformRoleEnum | None = None

class ChangePasswordDTO(BaseModel):
    old_password: str
    new_password: str

class SecondaryEmailDTO(BaseModel):
    email: EmailStr

class DiscordDTO(BaseModel):
    discord_id: int