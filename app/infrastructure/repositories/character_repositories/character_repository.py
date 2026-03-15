#app/infrastructure/repositories/character_repositories/character_repository.py
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.entities import Character, User, Game, GameSystem
from app.domain.repositories import ICharacterRepository
from app.infrastructure.models import CharacterModel
from app.infrastructure.repositories.exception_handlers import handle_user_integrity_error
from app.utils import Mapper


class CharacterRepository(ICharacterRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _active(stmt):
        """Фильтрует запрос, исключая мягко удалённых персонажей"""
        return stmt.where(CharacterModel.deleted_at.is_(None))

    async def create(self, character: Character) -> Character:
        model = Mapper.entity_to_model(character, CharacterModel)
        self.session.add(model)
        try:
            await self.session.flush()
        except IntegrityError as e:
            handle_user_integrity_error(e)
        return Mapper.model_to_entity(model, Character)

    async def get_by_id(self, character_id: UUID) -> Optional[Character]:
        stmt = self._active(
            select(CharacterModel).where(CharacterModel.id == character_id)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Mapper.model_to_entity(model, Character)

    async def get_by_id_with_relations(self, character_id: UUID) -> Optional[Character]:
        stmt = self._active(
            select(CharacterModel)
            .where(CharacterModel.id == character_id)
            .options(
                joinedload(CharacterModel.author),
                joinedload(CharacterModel.game),
                joinedload(CharacterModel.game_system),
            )
        )
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        if not model:
            return None
        return Mapper.model_to_entity_with_relations(
            model,
            Character,
            relations={
                "author": (model.author, User),
                "game": (model.game, Game),
                "game_system": (model.game_system, GameSystem),
            }
        )

    async def get_all_by_user_id(self, user_id: UUID, offset: int, limit: int, include_deleted: bool = False,
                                 only_deleted: bool = False) -> list[Character]:
        stmt = select(CharacterModel).where(CharacterModel.user_id == user_id)
        if only_deleted:
            stmt = stmt.where(CharacterModel.deleted_at.isnot(None))
        elif not include_deleted:
            stmt = stmt.where(CharacterModel.deleted_at.is_(None))
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, Character) for m in result.scalars().all()]

    async def count_by_user_id(self, user_id: UUID) -> int:
        stmt = self._active(
            select(func.count()).select_from(CharacterModel)
            .where(CharacterModel.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_game_id(self, game_id: UUID, offset: int, limit: int) -> list[Character]:
        stmt = self._active(
            select(CharacterModel).where(CharacterModel.game_id == game_id)
        ).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, Character) for m in result.scalars().all()]

    async def count_by_game_id(self, game_id: UUID) -> int:
        stmt = self._active(
            select(func.count()).select_from(CharacterModel)
            .where(CharacterModel.game_id == game_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_id_and_game_id(self, character_id: UUID, game_id: UUID) -> Optional[Character]:
        stmt = self._active(
            select(CharacterModel)
            .where(CharacterModel.id == character_id)
            .where(CharacterModel.game_id == game_id)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Mapper.model_to_entity(model, Character)

    async def get_by_game_id_and_user_ids(
            self, game_id: UUID, user_ids: list[UUID], offset: int, limit: int
    ) -> list[Character]:
        result = await self.session.execute(
            select(CharacterModel)
            .where(
                CharacterModel.game_id == game_id,
                CharacterModel.user_id.in_(user_ids)
            )
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_game_id_and_user_ids(
            self, game_id: UUID, user_ids: list[UUID]
    ) -> int:
        result = await self.session.execute(
            select(func.count())
            .where(
                CharacterModel.game_id == game_id,
                CharacterModel.user_id.in_(user_ids)
            )
        )
        return result.scalar()

    async def attach_to_game(self, character_id: UUID, game_id: UUID) -> Character:
        stmt = (
            update(CharacterModel)
            .where(CharacterModel.id == character_id)
            .where(CharacterModel.deleted_at.is_(None))
            .values(game_id=game_id)
            .execution_options(synchronize_session="fetch")
            .returning(CharacterModel)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        return Mapper.model_to_entity(model, Character)

    async def detach_from_game(self, character_id: UUID) -> None:
        stmt = (
            update(CharacterModel)
            .where(CharacterModel.id == character_id)
            .where(CharacterModel.deleted_at.is_(None))
            .values(game_id=None)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)

    async def update(self, character: Character) -> Character:
        stmt = (
            update(CharacterModel)
            .where(CharacterModel.id == character.id)
            .where(CharacterModel.deleted_at.is_(None))
            .values(
                name=character.name,
                user_id=character.user_id,
                game_id=character.game_id,
                avatar=character.avatar,
                game_system_id=character.game_system_id,
                sheet_data=character.sheet_data,
            )
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)
        return character

    async def soft_delete(self, character_id: UUID) -> None:
        stmt = (
            update(CharacterModel)
            .where(CharacterModel.id == character_id)
            .where(CharacterModel.deleted_at.is_(None))
            .values(deleted_at=func.now())
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)

    async def restore(self, character_id: UUID) -> None:
        stmt = (
            update(CharacterModel)
            .where(CharacterModel.id == character_id)
            .where(CharacterModel.deleted_at.isnot(None))
            .values(deleted_at=None)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)

    async def delete(self, character_id: UUID) -> None:
        stmt = delete(CharacterModel).where(CharacterModel.id == character_id)
        await self.session.execute(stmt)

