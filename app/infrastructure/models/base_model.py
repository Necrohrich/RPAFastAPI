#app/infrastructure/models/base_model.py
import uuid

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class BaseModel(AsyncAttrs, DeclarativeBase):
    """Базовая модель со стандартными полями"""

    __abstract__ = True  # НЕ создаёт таблицу в БД!

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)