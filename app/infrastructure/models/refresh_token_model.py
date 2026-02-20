# app/infrastructure/models/refresh_token_model.py
from datetime import datetime
from uuid import UUID

from sqlalchemy import String, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models import BaseModel

class RefreshTokenModel(BaseModel):
    """
    Модель, описывающая refresh-токены пользователей

        Хранит refresh-токены для аутентификации и ротации сессий.

        Ключевые поля:
            * user_id — владелец токена (FK → users.id)
            * token_hash — уникальный хэш токена
            * expires_at — время истечения токена
            * revoked_at — время ручного отзыва токена
            * device_info — информация об устройстве
            * replaced_by_token_id — ссылка на токен, которым заменён текущий
    """
    __tablename__ = "refresh_tokens"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # часто ищем токены по пользователю
    )

    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,   # один хэш — один токен
        index=True,    # быстрый поиск при аутентификации
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,  # удобно для очистки просроченных токенов
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,  # если часто проверяешь revoked
    )

    device_info: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
    )

    replaced_by_token_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"),
        nullable=True,
        index=True,  # для отслеживания цепочки ротации
    )

    __table_args__ = (
        Index(
            "ix_refresh_tokens_active",
            "user_id",
            postgresql_where=text("revoked_at IS NULL"),
        ),
    )