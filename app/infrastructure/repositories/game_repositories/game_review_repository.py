# app/infrastructure/repositories/game_review_repositories/game_review_repository.py
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, delete, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.game_review import GameReview
from app.domain.enums.review_status_enum import ReviewStatusEnum
from app.domain.repositories.game_repositories.game_review_repository import IGameReviewRepository
from app.infrastructure.models.game_review_model import GameReviewModel
from app.infrastructure.repositories.exception_handlers import handle_user_integrity_error
from app.utils import Mapper


class GameReviewRepository(IGameReviewRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _apply_status_filter(stmt, statuses: Optional[list[ReviewStatusEnum]]):
        """Применяет фильтр по статусам. По умолчанию — только SEND."""
        if statuses is not None:
            return stmt.where(GameReviewModel.status.in_(statuses))
        return stmt.where(GameReviewModel.status == ReviewStatusEnum.SEND)

    @staticmethod
    def _apply_deleted_filter(stmt, include_deleted: bool):
        if not include_deleted:
            return stmt.where(GameReviewModel.deleted_at.is_(None))
        return stmt

    # ── CRUD ──────────────────────────────────────────────────────────────────

    async def create(self, review: GameReview) -> GameReview:
        model = Mapper.entity_to_model(review, GameReviewModel)
        self.session.add(model)
        try:
            await self.session.flush()
        except IntegrityError as e:
            handle_user_integrity_error(e)
        return Mapper.model_to_entity(model, GameReview)

    async def get_by_id(
        self,
        review_id: UUID,
        include_deleted: bool = False,
    ) -> Optional[GameReview]:
        stmt = select(GameReviewModel).where(GameReviewModel.id == review_id)
        stmt = self._apply_deleted_filter(stmt, include_deleted)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Mapper.model_to_entity(model, GameReview)

    async def update(self, review: GameReview) -> GameReview:
        stmt = (
            update(GameReviewModel)
            .where(GameReviewModel.id == review.id)
            .where(GameReviewModel.deleted_at.is_(None))
            .values(
                status=review.status,
                anonymity=review.anonymity,
                rating=review.rating,
                comment=review.comment,
                best_scenes=review.best_scenes,
                best_npc=review.best_npc,
                best_player_id=review.best_player_id,
            )
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)
        return review

    async def soft_delete(self, review_id: UUID) -> None:
        stmt = (
            update(GameReviewModel)
            .where(GameReviewModel.id == review_id)
            .where(GameReviewModel.deleted_at.is_(None))
            .values(deleted_at=func.now())
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)

    async def restore(self, review_id: UUID) -> None:
        stmt = (
            update(GameReviewModel)
            .where(GameReviewModel.id == review_id)
            .where(GameReviewModel.deleted_at.isnot(None))
            .values(deleted_at=None)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)

    async def delete(self, review_id: UUID) -> None:
        stmt = delete(GameReviewModel).where(GameReviewModel.id == review_id)
        await self.session.execute(stmt)

    # ── Bulk операции ─────────────────────────────────────────────────────────

    async def soft_delete_by_session_id(self, session_id: UUID) -> None:
        stmt = (
            update(GameReviewModel)
            .where(GameReviewModel.session_id == session_id)
            .where(GameReviewModel.deleted_at.is_(None))
            .values(deleted_at=func.now())
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)

    # ── Выборки по игре ───────────────────────────────────────────────────────

    async def get_by_game_id(
        self,
        game_id: UUID,
        offset: int,
        limit: int,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReview]:
        stmt = select(GameReviewModel).where(GameReviewModel.game_id == game_id)
        stmt = self._apply_status_filter(stmt, statuses)
        stmt = self._apply_deleted_filter(stmt, include_deleted)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, GameReview) for m in result.scalars().all()]

    async def count_by_game_id(
        self,
        game_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(GameReviewModel)
            .where(GameReviewModel.game_id == game_id)
        )
        stmt = self._apply_status_filter(stmt, statuses)
        stmt = self._apply_deleted_filter(stmt, include_deleted)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_list_by_game_id(
        self,
        game_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReview]:
        stmt = select(GameReviewModel).where(GameReviewModel.game_id == game_id)
        stmt = self._apply_status_filter(stmt, statuses)
        stmt = self._apply_deleted_filter(stmt, include_deleted)
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, GameReview) for m in result.scalars().all()]

    # ── Выборки по сессии ─────────────────────────────────────────────────────

    async def get_by_session_id(
        self,
        session_id: UUID,
        offset: int,
        limit: int,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReview]:
        stmt = select(GameReviewModel).where(GameReviewModel.session_id == session_id)
        stmt = self._apply_status_filter(stmt, statuses)
        stmt = self._apply_deleted_filter(stmt, include_deleted)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, GameReview) for m in result.scalars().all()]

    async def count_by_session_id(
        self,
        session_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(GameReviewModel)
            .where(GameReviewModel.session_id == session_id)
        )
        stmt = self._apply_status_filter(stmt, statuses)
        stmt = self._apply_deleted_filter(stmt, include_deleted)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_list_by_session_id(
        self,
        session_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReview]:
        stmt = select(GameReviewModel).where(GameReviewModel.session_id == session_id)
        stmt = self._apply_status_filter(stmt, statuses)
        stmt = self._apply_deleted_filter(stmt, include_deleted)
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, GameReview) for m in result.scalars().all()]

    # ── Выборки по пользователю ───────────────────────────────────────────────

    async def get_by_user_id(
        self,
        user_id: UUID,
        offset: int,
        limit: int,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReview]:
        stmt = select(GameReviewModel).where(GameReviewModel.user_id == user_id)
        stmt = self._apply_status_filter(stmt, statuses)
        stmt = self._apply_deleted_filter(stmt, include_deleted)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, GameReview) for m in result.scalars().all()]

    async def count_by_user_id(
        self,
        user_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(GameReviewModel)
            .where(GameReviewModel.user_id == user_id)
        )
        stmt = self._apply_status_filter(stmt, statuses)
        stmt = self._apply_deleted_filter(stmt, include_deleted)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_list_by_user_id(
        self,
        user_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReview]:
        stmt = select(GameReviewModel).where(GameReviewModel.user_id == user_id)
        stmt = self._apply_status_filter(stmt, statuses)
        stmt = self._apply_deleted_filter(stmt, include_deleted)
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, GameReview) for m in result.scalars().all()]

    # ── Точечные выборки ──────────────────────────────────────────────────────

    async def get_by_game_id_and_user_id(
        self,
        game_id: UUID,
        user_id: UUID,
        include_deleted: bool = False,
    ) -> list[GameReview]:
        stmt = select(GameReviewModel).where(
            GameReviewModel.game_id == game_id,
            GameReviewModel.user_id == user_id,
        )
        stmt = self._apply_deleted_filter(stmt, include_deleted)
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, GameReview) for m in result.scalars().all()]

    async def get_by_session_id_and_user_id(
        self,
        session_id: UUID,
        user_id: UUID,
        include_deleted: bool = False,
    ) -> Optional[GameReview]:
        stmt = select(GameReviewModel).where(
            GameReviewModel.session_id == session_id,
            GameReviewModel.user_id == user_id,
        )
        stmt = self._apply_deleted_filter(stmt, include_deleted)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Mapper.model_to_entity(model, GameReview)

    # ── Статистика ────────────────────────────────────────────────────────────

    async def get_best_npc_stats(
        self, game_id: UUID
    ) -> list[tuple[str, int]]:
        """
        Разворачивает JSONB-массив best_npc и считает упоминания без учёта регистра.

        Использует PostgreSQL-специфичную функцию jsonb_array_elements_text.
        Это намеренная привязка к PostgreSQL — весь проект уже её использует
        (JSONB-колонки, pg_insert, postgresql_where в индексах).

        Алгоритм:
            1. jsonb_array_elements_text(best_npc) — разворачивает массив в строки
            2. lower() — нормализуем регистр
            3. GROUP BY + COUNT — считаем упоминания
            4. ORDER BY count DESC
        """
        stmt = text("""
            SELECT lower(npc_name) AS npc, COUNT(*) AS cnt
            FROM game_reviews,
                 jsonb_array_elements_text(best_npc) AS npc_name
            WHERE game_id = :game_id
              AND status = 'send'
              AND deleted_at IS NULL
              AND best_npc IS NOT NULL
            GROUP BY lower(npc_name)
            ORDER BY cnt DESC
        """)
        result = await self.session.execute(stmt, {"game_id": str(game_id)})
        return [(row[0], row[1]) for row in result.all()]

    async def get_best_scenes_stats(
        self, game_id: UUID
    ) -> list[tuple[str, str, int]]:
        """
        Разворачивает JSONB-объект best_scenes {scene_name: scene_type}
        и считает упоминания без учёта регистра названия сцены.

        Использует PostgreSQL-специфичную функцию jsonb_each_text.
        Это намеренная привязка к PostgreSQL — весь проект уже её использует.

        Алгоритм:
            1. jsonb_each_text(best_scenes) — разворачивает объект в (key, value)
               key = название сцены, value = тип сцены
            2. lower(key) — нормализуем регистр
            3. GROUP BY lower(key), value + COUNT
            4. ORDER BY count DESC
        """
        stmt = text("""
            SELECT lower(scene_name) AS scene, scene_type, COUNT(*) AS cnt
            FROM game_reviews,
                 jsonb_each_text(best_scenes) AS scenes(scene_name, scene_type)
            WHERE game_id = :game_id
              AND status = 'send'
              AND deleted_at IS NULL
              AND best_scenes IS NOT NULL
            GROUP BY lower(scene_name), scene_type
            ORDER BY cnt DESC
        """)
        result = await self.session.execute(stmt, {"game_id": str(game_id)})
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def get_best_players_stats(
        self, game_id: UUID
    ) -> list[tuple[UUID, int]]:
        stmt = (
            select(GameReviewModel.best_player_id, func.count().label("cnt"))
            .where(
                GameReviewModel.game_id == game_id,
                GameReviewModel.status == ReviewStatusEnum.SEND,
                GameReviewModel.deleted_at.is_(None),
                GameReviewModel.best_player_id.isnot(None),
            )
            .group_by(GameReviewModel.best_player_id)
            .order_by(func.count().desc())
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_ratings_by_game_id(
        self, game_id: UUID
    ) -> list[str]:
        stmt = (
            select(GameReviewModel.rating)
            .where(
                GameReviewModel.game_id == game_id,
                GameReviewModel.status == ReviewStatusEnum.SEND,
                GameReviewModel.deleted_at.is_(None),
                GameReviewModel.rating.isnot(None),
            )
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def count_distinct_sessions_by_game_id(self, game_id: UUID) -> int:
        stmt = (
            select(func.count(GameReviewModel.session_id.distinct()))
            .where(
                GameReviewModel.game_id == game_id,
                GameReviewModel.status == ReviewStatusEnum.SEND,
                GameReviewModel.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def count_distinct_users_by_game_id(self, game_id: UUID) -> int:
        stmt = (
            select(func.count(GameReviewModel.user_id.distinct()))
            .where(
                GameReviewModel.game_id == game_id,
                GameReviewModel.status == ReviewStatusEnum.SEND,
                GameReviewModel.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()