#app/infrastructure/repositories/character_repositories/character_repository.py
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.entities import Character
from app.domain.repositories import ICharacterRepository
from app.infrastructure.models import CharacterModel
from app.infrastructure.repositories.exception_handlers import handle_user_integrity_error
from app.utils import Mapper


class CharacterRepository(ICharacterRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, character: Character) -> Character:
        model = Mapper.entity_to_model(character, CharacterModel)
        self.session.add(model)
        try:
            await self.session.flush()
        except IntegrityError as e:
            handle_user_integrity_error(e)
        return Mapper.model_to_entity(model, Character)

    async def get_by_id(self, character_id: UUID) -> Optional[Character]:
        model = await self.session.get(CharacterModel, character_id)
        if not model:
            return None
        return Mapper.model_to_entity(model, Character)

    async def get_by_id_with_relations(self, character_id: UUID) -> Optional[Character]:
        stmt = (
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
        return Mapper.model_to_entity(model, Character)

    async def get_by_user_id(self, user_id: UUID) -> list[Character]:
        stmt = select(CharacterModel).where(
            CharacterModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [Mapper.model_to_entity(model, Character) for model in models]

    async def get_by_game_id(self, game_id: UUID) -> list[Character]:
        stmt = select(CharacterModel).where(
            CharacterModel.game_id == game_id
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [Mapper.model_to_entity(model, Character) for model in models]

    async def update(self, character: Character) -> Character:
        stmt = (
            update(CharacterModel)
            .where(CharacterModel.id == character.id)
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

    async def delete(self, character_id: UUID) -> None:
        stmt = delete(CharacterModel).where(
            CharacterModel.id == character_id
        )
        await self.session.execute(stmt)