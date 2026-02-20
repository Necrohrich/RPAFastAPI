#app/domain/repositories/auth_repositories/discord_repositories.py
from abc import ABC, abstractmethod
from uuid import UUID


class IDiscordRepository(ABC):

    @abstractmethod
    async def attach_priority(self, user_id: UUID, discord_id: int) -> None:
        pass

    @abstractmethod
    async def attach_secondary(self, user_id: UUID, discord_id: int) -> None:
        pass

    @abstractmethod
    async def get_user_by_discord_id(self, discord_id: int):
        pass