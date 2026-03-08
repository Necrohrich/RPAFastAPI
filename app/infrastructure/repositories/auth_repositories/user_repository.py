#app/infrastructure/repositories/auth_repositories/user_repository.py
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import User, Game, Character
from app.domain.enums import PlatformRoleEnum, PlayerStatusEnum
from app.domain.repositories import IUserRepository
from app.infrastructure.models import UserModel, RefreshTokenModel, CharacterModel, GameModel, GamePlayerModel
from app.infrastructure.repositories.exception_handlers import handle_user_integrity_error
from app.utils import Mapper

class UserRepository(IUserRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: User) -> None:
        model = Mapper.entity_to_model(user, UserModel)
        self.session.add(model)
        try:
            await self.session.flush()
        except IntegrityError as e:
            handle_user_integrity_error(e)

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(UserModel).where(
            UserModel.primary_email == email
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return Mapper.model_to_entity(model, User)

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        model = await self.session.get(UserModel, user_id)

        if not model:
            return None

        return Mapper.model_to_entity(model, User)

    async def attach_secondary_email(self, user_id: UUID, email: str) -> None:
        model = await self.session.get(UserModel, user_id)
        if model:
            model.secondary_email = email

    async def update_password(self, user_id: UUID, password_hash: str) -> None:
        model = await self.session.get(UserModel, user_id)
        if model:
            model.password_hash = password_hash

    async def update_role(self, user_id: UUID, role: PlatformRoleEnum) -> None:
        model = await self.session.get(UserModel, user_id)
        if model:
            model.platform_role = role

    async def update_token_version(self, user_id: UUID, version: int) -> None:
        stmt_user = (
            update(UserModel)
            .where(UserModel.id == user_id, UserModel.token_version < version)
            .values(token_version=version)
        )
        await self.session.execute(stmt_user)

        stmt_revoke = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked_at.is_(None)
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt_revoke)

    async def get_my_games(self, user_id: UUID, offset: int, limit: int) -> list[Game]:
        stmt = (
            select(GameModel)
            .where(GameModel.author_id == user_id)
            .where(GameModel.deleted_at.is_(None))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, Game) for m in result.scalars().all()]

    async def count_my_games(self, user_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(GameModel)
            .where(GameModel.author_id == user_id)
            .where(GameModel.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_participated_games(self, user_id: UUID, offset: int, limit: int) -> list[Game]:
        stmt = (
            select(GameModel)
            .join(GamePlayerModel, GamePlayerModel.game_id == GameModel.id)
            .where(GamePlayerModel.user_id == user_id)
            .where(GamePlayerModel.status == PlayerStatusEnum.ACCEPTED)
            .where(GameModel.deleted_at.is_(None))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, Game) for m in result.scalars().all()]

    async def count_participated_games(self, user_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(GamePlayerModel)
            .where(GamePlayerModel.user_id == user_id)
            .where(GamePlayerModel.status == PlayerStatusEnum.ACCEPTED)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_my_characters(self, user_id: UUID, offset: int, limit: int) -> list[Character]:
        stmt = (
            select(CharacterModel)
            .where(CharacterModel.user_id == user_id)
            .where(CharacterModel.deleted_at.is_(None))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [Mapper.model_to_entity(m, Character) for m in result.scalars().all()]

    async def count_my_characters(self, user_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(CharacterModel)
            .where(CharacterModel.user_id == user_id)
            .where(CharacterModel.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()