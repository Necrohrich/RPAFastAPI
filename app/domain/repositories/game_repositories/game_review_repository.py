# app/domain/repositories/game_repositories/game_review_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.game_review import GameReview
from app.domain.enums.review_status_enum import ReviewStatusEnum


class IGameReviewRepository(ABC):
    """
    Интерфейс репозитория для работы с игровыми отзывами.

    Базовые правила:
        - По умолчанию get-методы возвращают только SEND отзывы без deleted_at.
        - Параметры include_deleted, only_deleted, statuses позволяют выйти за это ограничение.
        - Статистические методы работают только с SEND + deleted_at IS NULL.

    Методы CRUD:
        * create — создаёт новый отзыв (статус CREATED)
        * get_by_id — возвращает отзыв по UUID
        * update — обновляет поля отзыва (только для CREATED)
        * soft_delete — проставляет deleted_at
        * restore — обнуляет deleted_at
        * delete — физически удаляет отзыв

    Методы выборки:
        * get_by_game_id — paginated список отзывов по игре
        * count_by_game_id — количество отзывов по игре
        * get_list_by_game_id — полный список (для Discord)
        * get_by_session_id — paginated список отзывов по сессии
        * count_by_session_id — количество отзывов по сессии
        * get_list_by_session_id — полный список (для Discord)
        * get_by_user_id — paginated список отзывов пользователя
        * count_by_user_id — количество отзывов пользователя
        * get_list_by_user_id — полный список (для Discord)
        * get_by_game_id_and_user_id — отзыв конкретного игрока в игре
        * get_by_session_id_and_user_id — отзыв конкретного игрока в сессии
        * get_send_by_session_id — все SEND отзывы сессии (для публикации)

    Методы для мягкого удаления при инвалидации сессии:
        * soft_delete_by_session_id — мягко удаляет все отзывы сессии

    Статистические методы (только SEND + not deleted):
        * get_best_npc_stats — список (npc_name, count) по игре, сортировка по убыванию
        * get_best_scenes_stats — список (scene_name, scene_type, count) по игре
        * get_best_players_stats — список (user_id, count) по игре
        * get_ratings_by_game_id — список всех рейтингов SEND отзывов игры
        * count_distinct_sessions_by_game_id — число уникальных сессий с SEND отзывами
        * count_distinct_users_by_game_id — число уникальных игроков с SEND отзывами
    """

    # ── CRUD ─────────────────────────────────────────────────────────────────

    @abstractmethod
    async def create(self, review: GameReview) -> GameReview: ...

    @abstractmethod
    async def get_by_id(
        self,
        review_id: UUID,
        include_deleted: bool = False,
    ) -> Optional[GameReview]: ...

    @abstractmethod
    async def update(self, review: GameReview) -> GameReview: ...

    @abstractmethod
    async def soft_delete(self, review_id: UUID) -> None: ...

    @abstractmethod
    async def restore(self, review_id: UUID) -> None: ...

    @abstractmethod
    async def delete(self, review_id: UUID) -> None: ...

    # ── Bulk операции ─────────────────────────────────────────────────────────

    @abstractmethod
    async def soft_delete_by_session_id(self, session_id: UUID) -> None:
        """Мягко удаляет все отзывы сессии (вызывается при INVALID сессии)."""
        ...

    # ── Выборки по игре ───────────────────────────────────────────────────────

    @abstractmethod
    async def get_by_game_id(
        self,
        game_id: UUID,
        offset: int,
        limit: int,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReview]: ...

    @abstractmethod
    async def count_by_game_id(
        self,
        game_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> int: ...

    @abstractmethod
    async def get_list_by_game_id(
        self,
        game_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReview]: ...

    # ── Выборки по сессии ─────────────────────────────────────────────────────

    @abstractmethod
    async def get_by_session_id(
        self,
        session_id: UUID,
        offset: int,
        limit: int,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReview]: ...

    @abstractmethod
    async def count_by_session_id(
        self,
        session_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> int: ...

    @abstractmethod
    async def get_list_by_session_id(
        self,
        session_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReview]: ...

    # ── Выборки по пользователю ───────────────────────────────────────────────

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: UUID,
        offset: int,
        limit: int,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReview]: ...

    @abstractmethod
    async def count_by_user_id(
        self,
        user_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> int: ...

    @abstractmethod
    async def get_list_by_user_id(
        self,
        user_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReview]: ...

    # ── Точечные выборки ──────────────────────────────────────────────────────

    @abstractmethod
    async def get_by_game_id_and_user_id(
        self,
        game_id: UUID,
        user_id: UUID,
        include_deleted: bool = False,
    ) -> list[GameReview]:
        """Все отзывы пользователя в рамках игры (по разным сессиям)."""
        ...

    @abstractmethod
    async def get_by_session_id_and_user_id(
        self,
        session_id: UUID,
        user_id: UUID,
        include_deleted: bool = False,
    ) -> Optional[GameReview]:
        """Отзыв пользователя на конкретную сессию (уникален)."""
        ...

    # ── Статистика ────────────────────────────────────────────────────────────

    @abstractmethod
    async def get_best_npc_stats(
        self, game_id: UUID
    ) -> list[tuple[str, int]]:
        """
        Возвращает список (npc_name, count) для SEND отзывов игры.
        Имена сравниваются без учёта регистра.
        Сортировка: count DESC.
        """
        ...

    @abstractmethod
    async def get_best_scenes_stats(
        self, game_id: UUID
    ) -> list[tuple[str, str, int]]:
        """
        Возвращает список (scene_name, scene_type, count) для SEND отзывов игры.
        Имена сцен сравниваются без учёта регистра.
        Сортировка: count DESC.
        """
        ...

    @abstractmethod
    async def get_best_players_stats(
        self, game_id: UUID
    ) -> list[tuple[UUID, int]]:
        """
        Возвращает список (user_id, count) для SEND отзывов игры.
        Сортировка: count DESC.
        """
        ...

    @abstractmethod
    async def get_ratings_by_game_id(
        self, game_id: UUID
    ) -> list[str]:
        """
        Возвращает список значений rating из SEND отзывов игры.
        Используется сервисом для расчёта справедливой оценки.
        """
        ...

    @abstractmethod
    async def count_distinct_sessions_by_game_id(self, game_id: UUID) -> int:
        """Число уникальных сессий с хотя бы одним SEND отзывом."""
        ...

    @abstractmethod
    async def count_distinct_users_by_game_id(self, game_id: UUID) -> int:
        """Число уникальных игроков, написавших хотя бы один SEND отзыв."""
        ...