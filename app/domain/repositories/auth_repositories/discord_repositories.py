#app/domain/repositories/auth_repositories/discord_repositories.py
from abc import ABC, abstractmethod
from uuid import UUID


class IDiscordRepository(ABC):
    """
    Интерфейс репозитория для работы с Discord аккаунтами пользователей.

        Предоставляет методы для привязки Discord ID к пользователю и получения пользователя по Discord ID.

        Методы:
            * attach_priority — привязывает основной (priority) Discord ID к пользователю
            * attach_secondary — привязывает вторичный Discord ID
            * get_user_by_discord_id — возвращает пользователя по Discord ID
    """

    @abstractmethod
    async def attach_priority(self, user_id: UUID, discord_id: int) -> None:
        pass

    @abstractmethod
    async def attach_secondary(self, user_id: UUID, discord_id: int) -> None:
        pass

    @abstractmethod
    async def get_user_by_discord_id(self, discord_id: int):
        pass