#app/infrastructure/repositories/game_repositories/game_system_repository.py
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import GameSystem
from app.domain.repositories import IGameSystemRepository
from app.infrastructure.models import GameSystemModel
from app.infrastructure.repositories.exception_handlers import handle_user_integrity_error
from app.utils import Mapper


class GameSystemRepository(IGameSystemRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, game_system: GameSystem) -> GameSystem:
        model =  Mapper.entity_to_model(game_system, GameSystemModel)
        self.session.add(model)
        try:
            await self.session.flush()
        except IntegrityError as e:
            handle_user_integrity_error(e)
        return Mapper.model_to_entity(model, GameSystem)

    async def get_by_id(self, game_system_id: UUID) -> Optional[GameSystem]:
        model = await self.session.get(GameSystemModel, game_system_id)
        if not model:
            return None
        return Mapper.model_to_entity(model, GameSystem)

    async def get_by_name(self, name: str) -> Optional[GameSystem]:
        stmt = select(GameSystemModel).where(
            GameSystemModel.name == name
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Mapper.model_to_entity(model, GameSystem)

    async def get_all(self) -> list[GameSystem]:
        stmt = select(GameSystemModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [Mapper.model_to_entity(model, GameSystem) for model in models]

    async def update(self, game_system: GameSystem) -> GameSystem:
        stmt = (
            update(GameSystemModel)
            .where(GameSystemModel.id == game_system.id)
            .values(
                name=game_system.name,
                description=game_system.description,
            )
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)
        return game_system

    async def delete(self, game_system_id: UUID) -> None:
        stmt = delete(GameSystemModel).where(
            GameSystemModel.id == game_system_id
        )
        await self.session.execute(stmt)