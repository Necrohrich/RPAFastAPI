# app/domain/repositories/auth_repositories/token_repository.py
from abc import ABC
from uuid import UUID
from typing import Optional
from app.domain.entities.refresh_token import RefreshToken

class ITokenRepository(ABC):
    """
    Интерфейс репозитория для работы с refresh-токенами.

    Поддерживает:
        - Создание токенов с возможностью указания устройства и ротации
        - Получение токена по хэшу
        - Отзыв одного или всех токенов пользователя
        - Удаление просроченных токенов
    """

    async def create(self, token: RefreshToken) -> None:
        """
        Создаёт и сохраняет новый refresh-токен.

        Args:
            token: переданный объект RefreshToken

        Returns:
            bool: Успех создания токена
        """
        pass

    async def get(self, token_hash: str) -> Optional[RefreshToken]:
        """
        Получает refresh-токен по его хэшу.

        Args:
            token_hash: Хэш токена

        Returns:
            RefreshToken или None, если токен не найден
        """
        pass

    async def revoke(self, token_hash: str) -> None:
        """
        Отзывает один refresh-токен, устанавливая revoked_at.

        Args:
            token_hash: Хэш токена
        """
        pass

    async def revoke_all(self, user_id: UUID) -> None:
        """
        Отзывает все активные токены пользователя (revoked_at IS NULL).

        Args:
            user_id: ID пользователя
        """
        pass

    async def delete_expired(self) -> None:
        """
        Удаляет все refresh-токены, у которых expires_at < текущего времени
        """
        pass