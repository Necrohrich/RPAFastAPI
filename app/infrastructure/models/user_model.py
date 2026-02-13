#app/infrastructure/models/user_model.py
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, BigInteger
from sqlalchemy import Enum as SQLEnum

from app.domain.enums.platform_role_enum import PlatformRoleEnum
from app.infrastructure.models.base_model import BaseModel

class UserModel(BaseModel):
    """Модель, описывающая пользователя"""

    primary_email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    secondary_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_discord_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    secondary_discord_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    platform_role: Mapped[Optional[PlatformRoleEnum]] = mapped_column(
        SQLEnum(PlatformRoleEnum, name="platform_role_enum"), nullable=True
    )
