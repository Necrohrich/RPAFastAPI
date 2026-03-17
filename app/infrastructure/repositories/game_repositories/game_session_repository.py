# app/infrastructure/repositories/game_repositories/game_session_repository.py
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import GameSession
from app.domain.enums import GameSessionStatusEnum
from app.domain.repositories import IGameSessionRepository
from app.infrastructure.models import GameSessionModel
from app.utils import Mapper

# Статусы, которые не учитываются при нумерации сессий
_INVALID_STATUSES = (GameSessionStatusEnum.CANCELED, GameSessionStatusEnum.INVALID)


class GameSessionRepository(IGameSessionRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _valid(stmt):
        """Фильтрует запрос, оставляя только действительные сессии
        (не CANCELED и не IGNORED/INVALID)."""
        return stmt.where(
            GameSessionModel.status.notin_(_INVALID_STATUSES)
        )

    # ── write ─────────────────────────────────────────────────────────────────

    async def create(self, session: GameSession) -> GameSession:
        model = Mapper.entity_to_model(session, GameSessionModel)
        self.session.add(model)
        await self.session.flush()
        return Mapper.model_to_entity(model, GameSession)

    async def update(self, session: GameSession) -> GameSession:
        stmt = (
            update(GameSessionModel)
            .where(GameSessionModel.id == session.id)
            .values(
                title=session.title,
                description=session.description,
                image_url=session.image_url,
                started_at=session.started_at,
                ended_at=session.ended_at,
            )
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)
        return session

    async def update_status(
        self,
        session_id: UUID,
        status: GameSessionStatusEnum,
    ) -> GameSession:
        stmt = (
            update(GameSessionModel)
            .where(GameSessionModel.id == session_id)
            .values(status=status)
            .execution_options(synchronize_session="fetch")
            .returning(GameSessionModel)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        return Mapper.model_to_entity(model, GameSession)

    # ── read ──────────────────────────────────────────────────────────────────

    async def get_by_id(self, session_id: UUID) -> Optional[GameSession]:
        model = await self.session.get(GameSessionModel, session_id)
        if not model:
            return None
        return Mapper.model_to_entity(model, GameSession)

    async def get_by_game_id(
        self,
        game_id: UUID,
        offset: int,
        limit: int,
    ) -> list[GameSession]:
        stmt = (
            select(GameSessionModel)
            .where(GameSessionModel.game_id == game_id)
            .order_by(GameSessionModel.session_number)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, GameSession) for m in result.scalars().all()]

    async def count_by_game_id(self, game_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(GameSessionModel)
            .where(GameSessionModel.game_id == game_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_active_by_game_id(self, game_id: UUID) -> Optional[GameSession]:
        """Возвращает единственную ACTIVE сессию игры, если она есть."""
        stmt = select(GameSessionModel).where(
            GameSessionModel.game_id == game_id,
            GameSessionModel.status == GameSessionStatusEnum.ACTIVE,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Mapper.model_to_entity(model, GameSession)

    async def get_last_valid_by_game_id(self, game_id: UUID) -> Optional[GameSession]:
        """Возвращает последнюю действительную сессию (не CANCELED/INVALID)
        по убыванию session_number."""
        stmt = (
            self._valid(
                select(GameSessionModel).where(GameSessionModel.game_id == game_id)
            )
            .order_by(GameSessionModel.session_number.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Mapper.model_to_entity(model, GameSession)

    async def get_by_discord_event_id(
        self,
        discord_event_id: int,
    ) -> Optional[GameSession]:
        stmt = select(GameSessionModel).where(
            GameSessionModel.discord_event_id == discord_event_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Mapper.model_to_entity(model, GameSession)

    async def get_next_session_number(self, game_id: UUID) -> int:
        """Возвращает следующий порядковый номер для игры.

        Берёт MAX(session_number) среди действительных сессий (не CANCELED/INVALID).
        Если действительных сессий нет — возвращает 1.
        """
        stmt = (
            self._valid(
                select(func.max(GameSessionModel.session_number))
                .where(GameSessionModel.game_id == game_id)
            )
        )
        result = await self.session.execute(stmt)
        max_number = result.scalar_one_or_none()
        return (max_number or 0) + 1