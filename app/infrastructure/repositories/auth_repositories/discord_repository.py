#app/infrastructure/repositories/auth_repositories/discord_repository.py
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.repositories.auth_repositories.discord_repositories import IDiscordRepository
from app.infrastructure.models import UserModel
from app.utils.mapper import Mapper


class DiscordRepository(IDiscordRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def attach_priority(self, user_id: UUID, discord_id: int) -> None:
        model = await self.session.get(UserModel, user_id)
        if model:
            model.primary_discord_id = discord_id

    async def attach_secondary(self, user_id: UUID, discord_id: int) -> None:
        model = await self.session.get(UserModel, user_id)
        if model:
            model.secondary_discord_id = discord_id

    async def detach_secondary(self, user_id: UUID) -> None:
        model = await self.session.get(UserModel, user_id)
        if model:
            model.secondary_discord_id = None

    async def get_user_by_discord_id(self, discord_id: int) -> Optional[User]:
        stmt = select(UserModel).where(
            (UserModel.primary_discord_id == discord_id) |
            (UserModel.secondary_discord_id == discord_id)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return Mapper.model_to_entity(model, User)



