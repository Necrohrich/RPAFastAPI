# app/domain/repositories/discord_repositories/guild_settings_repository.py
from abc import ABC, abstractmethod
from typing import Optional


class IGuildDiscordSettingsRepository(ABC):
    """
    Интерфейс репозитория для работы с настройками Discord-серверов.

    Методы:
        * get_by_guild_id — возвращает настройки сервера в виде dict
          с ключами: guild_id, role_position_anchor_id
        * upsert — создаёт запись если не существует, иначе обновляет
        * delete — удаляет настройки сервера физически
    """

    @abstractmethod
    async def get_by_guild_id(self, guild_id: int) -> Optional[dict]:
        """Возвращает dict с ключами: guild_id, role_position_anchor_id — или None"""
        ...

    @abstractmethod
    async def upsert(
        self,
        guild_id: int,
        role_position_anchor_id: Optional[int],
    ) -> None: ...

    @abstractmethod
    async def delete(self, guild_id: int) -> None: ...