# app/infrastructure/repositories/discord_repositories/guild_settings_repository.py
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.discord_repositories.guild_settings_repository import IGuildDiscordSettingsRepository
from app.infrastructure.models import GuildDiscordSettingsModel

class GuildDiscordSettingsRepository(IGuildDiscordSettingsRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_guild_id(self, guild_id: int) -> Optional[dict]:
        stmt = select(GuildDiscordSettingsModel).where(
            GuildDiscordSettingsModel.guild_id == guild_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return {
            "guild_id": model.guild_id,
            "role_position_anchor_id": model.role_position_anchor_id,
        }

    async def upsert(
        self,
        guild_id: int,
        role_position_anchor_id: Optional[int],
    ) -> None:
        """INSERT ... ON CONFLICT (guild_id) DO UPDATE SET role_position_anchor_id = ..."""
        stmt = (
            pg_insert(GuildDiscordSettingsModel)
            .values(
                guild_id=guild_id,
                role_position_anchor_id=role_position_anchor_id,
            )
            .on_conflict_do_update(
                index_elements=["guild_id"],
                set_={"role_position_anchor_id": role_position_anchor_id},
            )
        )
        await self.session.execute(stmt)

    async def delete(self, guild_id: int) -> None:
        stmt = delete(GuildDiscordSettingsModel).where(
            GuildDiscordSettingsModel.guild_id == guild_id
        )
        await self.session.execute(stmt)