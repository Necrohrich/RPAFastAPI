# app/domain/entities/refresh_token.py
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from app.domain.entities.base_entity import BaseEntity

@dataclass(kw_only=True)
class RefreshToken(BaseEntity):
    """
        Domain Entity representing refresh token.

        Attributes:
            user_id (UUID): ID пользователя.
            token_hash (str): Хэш токена.
            expires_at (datetime): TTL.
            revoked_at (datetime): Время ручного отзыва.
            device_info (str):
            replaced_by_token_id (UUID): История ротации.
        """
    user_id: UUID
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None = None
    device_info: str = ""
    replaced_by_token_id: UUID | None = None