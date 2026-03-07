#app/infrastructure/repositories/game_repositories/game_repository.py
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, func, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.entities import Game, GamePlayer
from app.domain.enums import PlayerStatusEnum
from app.domain.repositories import IGameRepository
from app.infrastructure.models import GameModel, GamePlayerModel
from app.infrastructure.repositories.exception_handlers import handle_user_integrity_error
from app.utils import Mapper


class GameRepository(IGameRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _active(stmt):
        """Фильтрует запрос, исключая мягко удалённые игры"""
        return stmt.where(GameModel.deleted_at.is_(None))

    async def create(self, game: Game) -> Game:
        model = Mapper.entity_to_model(game, GameModel)
        self.session.add(model)
        try:
            await self.session.flush()
        except IntegrityError as e:
            handle_user_integrity_error(e)
        return Mapper.model_to_entity(model, Game)

    async def get_by_id(self, game_id: UUID) -> Optional[Game]:
        stmt = self._active(
            select(GameModel).where(GameModel.id == game_id)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Mapper.model_to_entity(model, Game)

    async def get_by_id_with_relations(self, game_id: UUID) -> Optional[Game]:
        stmt = self._active(
            select(GameModel)
            .where(GameModel.id == game_id)
            .options(
                joinedload(GameModel.author),
                joinedload(GameModel.game_system),
            )
        )
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        if not model:
            return None
        return Mapper.model_to_entity(model, Game)

    async def get_by_author_id(self, author_id: UUID) -> list[Game]:
        stmt = self._active(
            select(GameModel).where(GameModel.author_id == author_id)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [Mapper.model_to_entity(model, Game) for model in models]

    async def update(self, game: Game) -> Game:
        stmt = (
            update(GameModel)
            .where(GameModel.id == game.id)
            .where(GameModel.deleted_at.is_(None))
            .values(
                name=game.name,
                author_id=game.author_id,
                gm_id=game.gm_id,
                discord_role_id=game.discord_role_id,
                discord_main_channel_id=game.discord_main_channel_id,
                game_system_id=game.game_system_id,
            )
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)
        return game

    async def soft_delete(self, game_id: UUID) -> None:
        stmt = (
            update(GameModel)
            .where(GameModel.id == game_id)
            .where(GameModel.deleted_at.is_(None))
            .values(deleted_at=func.now())
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)

    async def restore(self, game_id: UUID) -> None:
        stmt = (
            update(GameModel)
            .where(GameModel.id == game_id)
            .where(GameModel.deleted_at.isnot(None))
            .values(deleted_at=None)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)

    async def delete(self, game_id: UUID) -> None:
        stmt = delete(GameModel).where(GameModel.id == game_id)
        await self.session.execute(stmt)

    # --- Игроки ---

    async def get_players(self, game_id: UUID, status: Optional[PlayerStatusEnum] = None) -> list[GamePlayer]:
        stmt = select(GamePlayerModel).where(GamePlayerModel.game_id == game_id)
        if status is not None:
            stmt = stmt.where(GamePlayerModel.status == status)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [Mapper.model_to_entity(model, GamePlayer) for model in models]

    async def add_player(self, game_player: GamePlayer) -> GamePlayer:
        model = Mapper.entity_to_model(game_player, GamePlayerModel)
        self.session.add(model)
        try:
            await self.session.flush()
        except IntegrityError as e:
            handle_user_integrity_error(e)
        return Mapper.model_to_entity(model, GamePlayer)

    async def update_player_status(self, game_id: UUID, user_id: UUID, status: PlayerStatusEnum) -> GamePlayer:
        stmt = (
            update(GamePlayerModel)
            .where(GamePlayerModel.game_id == game_id)
            .where(GamePlayerModel.user_id == user_id)
            .values(status=status)
            .execution_options(synchronize_session="fetch")
            .returning(GamePlayerModel)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        return Mapper.model_to_entity(model, GamePlayer)

    async def remove_player(self, game_id: UUID, user_id: UUID) -> None:
        stmt = delete(GamePlayerModel).where(
            GamePlayerModel.game_id == game_id,
            GamePlayerModel.user_id == user_id,
        )
        await self.session.execute(stmt)