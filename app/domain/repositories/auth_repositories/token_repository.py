# app/domain/repositories/auth_repositories/token_repository.py
from abc import ABC
from datetime import datetime
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

    async def create(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        device_info: str = "",
        replaced_by_token_id: Optional[UUID] = None,
    ) -> RefreshToken:
        """
        Создаёт и сохраняет новый refresh-токен.

        Args:
            user_id: ID пользователя
            token_hash: Хэш токена
            expires_at: Время истечения токена
            device_info: Информация об устройстве
            replaced_by_token_id: ID токена, который заменяет этот токен (ротация)

        Returns:
            RefreshToken: Созданный объект токена
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