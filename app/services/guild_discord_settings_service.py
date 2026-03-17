# app/services/guild_discord_settings_service.py
from typing import Optional

from app.domain.repositories.discord_repositories.guild_settings_repository import IGuildDiscordSettingsRepository
from app.dto.guild_discord_settings_dtos import GuildSettingsResponseDTO
from app.exceptions import GuildSettingsNotFoundException


class GuildDiscordSettingsService:
    """
    Application service responsible for Discord guild settings management.

    Handles:
        - Retrieving settings for a guild
        - Setting/updating the role position anchor
        - Clearing guild settings

    Does NOT:
        - Interact with Discord API directly (delegated to Discord layer)
        - Handle authentication or authorization
    """

    def __init__(self, repo: IGuildDiscordSettingsRepository):
        self.repo = repo

    async def get(self, guild_id: int) -> GuildSettingsResponseDTO:
        settings = await self.repo.get_by_guild_id(guild_id)
        if not settings:
            raise GuildSettingsNotFoundException()
        return GuildSettingsResponseDTO(**settings)

    async def set_role_anchor(
        self,
        guild_id: int,
        role_position_anchor_id: Optional[int],
    ) -> GuildSettingsResponseDTO:
        await self.repo.upsert(guild_id, role_position_anchor_id)
        return GuildSettingsResponseDTO(
            guild_id=guild_id,
            role_position_anchor_id=role_position_anchor_id,
        )

    async def clear(self, guild_id: int) -> None:
        await self.repo.delete(guild_id)