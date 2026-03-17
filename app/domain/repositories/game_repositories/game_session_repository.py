# app/domain/repositories/game_repositories/game_session_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities import GameSession
from app.domain.enums import GameSessionStatusEnum


class IGameSessionRepository(ABC):
    """
    Интерфейс репозитория для работы с игровыми сессиями.

    Управляет CRUD-операциями сессий и их статусами.

    Методы:
        * create — создаёт новую сессию и возвращает её с присвоенным ID
        * get_by_id — возвращает сессию по UUID
        * get_by_game_id — возвращает список сессий игры с пагинацией
        * count_by_game_id — возвращает число сессий игры
        * get_active_by_game_id — возвращает активную (ACTIVE) сессию игры, если есть
        * get_last_valid_by_game_id — возвращает последнюю действительную сессию игры
          (не CANCELED и не IGNORED), используется для определения следующего номера
        * update — обновляет поля сессии (title, description, image_url, started_at, ended_at)
        * update_status — обновляет статус сессии
        * get_by_discord_event_id — возвращает сессию по ID Discord Scheduled Event
        * get_next_session_number — возвращает следующий порядковый номер для игры
          (max session_number среди действительных сессий + 1, либо 1 если сессий нет)
    """

    @abstractmethod
    async def create(self, session: GameSession) -> GameSession: ...

    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> Optional[GameSession]: ...

    @abstractmethod
    async def get_by_game_id(
        self,
        game_id: UUID,
        offset: int,
        limit: int,
    ) -> list[GameSession]: ...

    @abstractmethod
    async def count_by_game_id(self, game_id: UUID) -> int: ...

    @abstractmethod
    async def get_active_by_game_id(self, game_id: UUID) -> Optional[GameSession]: ...

    @abstractmethod
    async def get_last_valid_by_game_id(self, game_id: UUID) -> Optional[GameSession]: ...

    @abstractmethod
    async def update(self, session: GameSession) -> GameSession: ...

    @abstractmethod
    async def update_status(
        self,
        session_id: UUID,
        status: GameSessionStatusEnum,
    ) -> GameSession: ...

    @abstractmethod
    async def get_by_discord_event_id(
        self,
        discord_event_id: int,
    ) -> Optional[GameSession]: ...

    @abstractmethod
    async def get_next_session_number(self, game_id: UUID) -> int: ...