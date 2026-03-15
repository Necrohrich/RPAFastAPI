#app/infrastructure/repositories/game_repositories/game_repository.py
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, func, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.entities import Game, GamePlayer, User, GameSystem
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

    async def get_by_id_include_deleted(self, game_id: UUID) -> Optional[Game]:
        stmt = select(GameModel).where(GameModel.id == game_id)
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
        return Mapper.model_to_entity_with_relations(
            model,
            Game,
            relations={
                "author": (model.author, User),
                "game_system": (model.game_system, GameSystem),
            }
        )

    async def get_by_author_id(
        self, author_id: UUID, offset: int, limit: int,
        include_deleted: bool = False, only_deleted: bool = False
    ) -> list[Game]:
        stmt = select(GameModel).where(GameModel.author_id == author_id)
        if only_deleted:
            stmt = stmt.where(GameModel.deleted_at.isnot(None))
        elif not include_deleted:
            stmt = stmt.where(GameModel.deleted_at.is_(None))
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, Game) for m in result.scalars().all()]

    async def count_by_author_id(
        self, author_id: UUID,
        include_deleted: bool = False, only_deleted: bool = False
    ) -> int:
        stmt = select(func.count()).select_from(GameModel).where(GameModel.author_id == author_id)
        if only_deleted:
            stmt = stmt.where(GameModel.deleted_at.isnot(None))
        elif not include_deleted:
            stmt = stmt.where(GameModel.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_name_and_author_id(self, author_id: UUID, name: str) -> Optional[Game]:
        stmt = self._active(
            select(GameModel)
            .where(GameModel.author_id == author_id)
            .where(GameModel.name == name),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Mapper.model_to_entity(model, Game)

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

    async def get_player(self, game_id: UUID, user_id: UUID) -> Optional[GamePlayer]:
        stmt = select(GamePlayerModel).where(
            GamePlayerModel.game_id == game_id,
            GamePlayerModel.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Mapper.model_to_entity(model, GamePlayer)

    async def get_players(self, game_id: UUID, status: Optional[PlayerStatusEnum], offset: int, limit: int) -> list[
        GamePlayer]:
        stmt = select(GamePlayerModel).where(GamePlayerModel.game_id == game_id)
        if status is not None:
            stmt = stmt.where(GamePlayerModel.status == status)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, GamePlayer) for m in result.scalars().all()]

    async def count_players(self, game_id: UUID, status: Optional[PlayerStatusEnum] = None) -> int:
        stmt = select(func.count()).select_from(GamePlayerModel).where(GamePlayerModel.game_id == game_id)
        if status is not None:
            stmt = stmt.where(GamePlayerModel.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one()

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