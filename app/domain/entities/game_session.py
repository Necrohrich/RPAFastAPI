#app/domain/entities/game_session.py

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from app.domain.entities.base_entity import BaseEntity
from app.domain.enums.game_session_status_enum import GameSessionStatusEnum

@dataclass(kw_only=True)
class GameSession(BaseEntity):
    """
    Domain Entity representing game session.

    Attributes:
        game_id (UUID): Уникальный идентификатор сущности.
        session_number (int): Номер игровой сессии.
        discord_event_id (int): ID привязанного Scheduled Event. Discord Only.
        title (str): Название игровой сессии.
        description (str): Описание игровой сессии.
        image_url (str): Ссылка на изображение игровой сессии.
        status (GameSessionStatusEnum): Статус игровой сессии.
        started_at (datetime): Время начала игровой сессии.
        ended_at (datetime): Время конца игровой сессии.
    """
    game_id: UUID
    session_number: int
    discord_event_id: int
    status: GameSessionStatusEnum = GameSessionStatusEnum.CREATED
    title: str = ""
    description: str = ""
    image_url: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None