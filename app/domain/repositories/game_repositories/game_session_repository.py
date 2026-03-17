# app/domain/repositories/game_repositories/game_session_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities import GameSession
from app.domain.enums import GameSessionStatusEnum


class IGameSessionRepository(ABC):
    """
    Интерфейс репозитория для работы с игровыми сессиями и их Discord-состоянием.

    Сессии:
        * create — создаёт новую сессию и возвращает её с присвоенным ID
        * get_by_id — возвращает сессию по UUID
        * get_by_game_id — возвращает список сессий игры с пагинацией
        * count_by_game_id — возвращает число сессий игры
        * get_completed_by_game_id — возвращает завершённые сессии игры с пагинацией
        * get_active_by_game_id — возвращает активную (ACTIVE) сессию игры, если есть
        * get_last_valid_by_game_id — возвращает последнюю действительную сессию игры
        * update — обновляет поля сессии (title, description, image_url, started_at, ended_at)
        * update_status — обновляет статус сессии
        * get_by_discord_event_id — возвращает сессию по ID Discord Scheduled Event
        * get_next_session_number — возвращает следующий порядковый номер для игры
        * link_discord_event — привязывает discord_event_id к сессии
        * find_game_id_by_event_title — ищет игру по частичному совпадению названия в строке события

    Discord-состояние (агрегат GameSession):
        * get_discord_state — возвращает Discord-состояние сессии
        * create_discord_state — создаёт запись Discord-состояния при старте сессии
        * update_discord_state — обновляет поля Discord-состояния
        * delete_discord_state — удаляет Discord-состояние (при завершении/отмене)
    """

    # ── Сессии ───────────────────────────────────────────────────────────────

    @abstractmethod
    async def create(self, session: GameSession) -> GameSession: ...

    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> Optional[GameSession]: ...

    @abstractmethod
    async def get_by_game_id(
        self, game_id: UUID, offset: int, limit: int,
    ) -> list[GameSession]: ...

    @abstractmethod
    async def count_by_game_id(self, game_id: UUID) -> int: ...

    @abstractmethod
    async def get_completed_by_game_id(
            self,
            game_id: UUID,
            offset: int,
            limit: int,
            from_number: Optional[int] = None,
            to_number: Optional[int] = None,
    ) -> list[GameSession]: ...

    @abstractmethod
    async def count_completed_by_game_id(
            self,
            game_id: UUID,
            from_number: Optional[int] = None,
            to_number: Optional[int] = None,
    ) -> int: ...

    @abstractmethod
    async def get_active_by_game_id(self, game_id: UUID) -> Optional[GameSession]: ...

    @abstractmethod
    async def get_last_valid_by_game_id(self, game_id: UUID) -> Optional[GameSession]: ...

    @abstractmethod
    async def update(self, session: GameSession) -> GameSession: ...

    @abstractmethod
    async def update_status(
        self, session_id: UUID, status: GameSessionStatusEnum,
    ) -> GameSession: ...

    @abstractmethod
    async def get_by_discord_event_id(self, discord_event_id: int) -> Optional[GameSession]: ...

    @abstractmethod
    async def get_next_session_number(self, game_id: UUID) -> int: ...

    @abstractmethod
    async def link_discord_event(self, session_id: UUID, discord_event_id: int) -> GameSession: ...

    @abstractmethod
    async def find_game_id_by_event_title(self, event_title: str) -> Optional[UUID]:
        """Ищет игру, название которой содержится в строке event_title (ILIKE).
        Возвращает game_id первого совпадения или None."""
        ...

    # ── Discord-состояние ────────────────────────────────────────────────────

    @abstractmethod
    async def get_discord_state(self, session_id: UUID) -> Optional[dict]:
        """Возвращает dict с ключами: attendance_message_id, temp_role_id, attending_user_ids"""
        ...

    @abstractmethod
    async def create_discord_state(
        self,
        session_id: UUID,
        attendance_message_id: Optional[int] = None,
        temp_role_id: Optional[int] = None,
        attending_user_ids: Optional[list[int]] = None,
    ) -> None: ...

    @abstractmethod
    async def update_discord_state(
        self,
        session_id: UUID,
        attendance_message_id: Optional[int] = None,
        temp_role_id: Optional[int] = None,
        attending_user_ids: Optional[list[int]] = None,
    ) -> None: ...

    @abstractmethod
    async def delete_discord_state(self, session_id: UUID) -> None: ...