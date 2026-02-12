#app/domain/entities/base_entity.py

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

@dataclass(kw_only=True) #kw_only решает конфликт полей при наследовании
class BaseEntity:
    """
    Domain Entity representing base entity.

    Attributes:
        id (UUID): Уникальный идентификатор сущности.
        created_at (datetime): Время создания сущности.
        updated_at (datetime): Время обновления сущности.
        deleted_at (datetime): Время удаления сущности.
    """

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: datetime | None = None