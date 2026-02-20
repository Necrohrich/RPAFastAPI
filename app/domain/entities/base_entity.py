#app/domain/entities/base_entity.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None