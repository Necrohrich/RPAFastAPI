# app/infrastructure/repositories/game_repositories/game_session_repository.py
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import GameSession
from app.domain.enums import GameSessionStatusEnum
from app.domain.repositories import IGameSessionRepository
from app.infrastructure.models import GameSessionModel, GameModel, GameSessionDiscordStateModel
from app.utils import Mapper

# Статусы, которые не учитываются при нумерации сессий
_INVALID_STATUSES = (GameSessionStatusEnum.CANCELED, GameSessionStatusEnum.INVALID)


class GameSessionRepository(IGameSessionRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _valid(stmt):
        """Фильтрует запрос, оставляя только действительные сессии."""
        return stmt.where(GameSessionModel.status.notin_(_INVALID_STATUSES))

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

    async def link_discord_event(self, session_id: UUID, discord_event_id: int) -> GameSession:
        stmt = (
            update(GameSessionModel)
            .where(GameSessionModel.id == session_id)
            .values(discord_event_id=discord_event_id)
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
        self, game_id: UUID, offset: int, limit: int,
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

    async def get_completed_by_game_id(
        self, game_id: UUID, offset: int, limit: int,
    ) -> list[GameSession]:
        stmt = (
            select(GameSessionModel)
            .where(GameSessionModel.game_id == game_id)
            .where(GameSessionModel.status == GameSessionStatusEnum.COMPLETED)
            .order_by(GameSessionModel.session_number)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, GameSession) for m in result.scalars().all()]

    async def count_completed_by_game_id(self, game_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(GameSessionModel)
            .where(GameSessionModel.game_id == game_id)
            .where(GameSessionModel.status == GameSessionStatusEnum.COMPLETED)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_active_by_game_id(self, game_id: UUID) -> Optional[GameSession]:
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

    async def get_by_discord_event_id(self, discord_event_id: int) -> Optional[GameSession]:
        stmt = select(GameSessionModel).where(
            GameSessionModel.discord_event_id == discord_event_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Mapper.model_to_entity(model, GameSession)

    async def get_next_session_number(self, game_id: UUID) -> int:
        stmt = self._valid(
            select(func.max(GameSessionModel.session_number))
            .where(GameSessionModel.game_id == game_id)
        )
        result = await self.session.execute(stmt)
        max_number = result.scalar_one_or_none()
        return (max_number or 0) + 1

    async def find_game_id_by_event_title(self, event_title: str) -> Optional[UUID]:
        """Ищет активную игру, название которой содержится в строке event_title (ILIKE)."""
        stmt = (
            select(GameModel.id)
            .where(GameModel.deleted_at.is_(None))
            .where(
                func.lower(func.cast(event_title, type_=None)).contains(
                    func.lower(GameModel.name)
                )
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Discord-состояние ────────────────────────────────────────────────────

    async def get_discord_state(self, session_id: UUID) -> Optional[dict]:
        stmt = select(GameSessionDiscordStateModel).where(
            GameSessionDiscordStateModel.session_id == session_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return {
            "attendance_message_id": model.attendance_message_id,
            "temp_role_id": model.temp_role_id,
            "attending_user_ids": model.attending_user_ids or [],
        }

    async def create_discord_state(
        self,
        session_id: UUID,
        attendance_message_id: Optional[int] = None,
        temp_role_id: Optional[int] = None,
        attending_user_ids: Optional[list[int]] = None,
    ) -> None:
        model = GameSessionDiscordStateModel(
            session_id=session_id,
            attendance_message_id=attendance_message_id,
            temp_role_id=temp_role_id,
            attending_user_ids=attending_user_ids or [],
        )
        self.session.add(model)
        await self.session.flush()

    async def update_discord_state(
        self,
        session_id: UUID,
        attendance_message_id: Optional[int] = None,
        temp_role_id: Optional[int] = None,
        attending_user_ids: Optional[list[int]] = None,
    ) -> None:
        values: dict = {}
        if attendance_message_id is not None:
            values["attendance_message_id"] = attendance_message_id
        if temp_role_id is not None:
            values["temp_role_id"] = temp_role_id
        if attending_user_ids is not None:
            values["attending_user_ids"] = attending_user_ids
        if not values:
            return
        stmt = (
            update(GameSessionDiscordStateModel)
            .where(GameSessionDiscordStateModel.session_id == session_id)
            .values(**values)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)

    async def delete_discord_state(self, session_id: UUID) -> None:
        stmt = delete(GameSessionDiscordStateModel).where(
            GameSessionDiscordStateModel.session_id == session_id
        )
        await self.session.execute(stmt)