#app/domain/repositories/auth_repositories/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.user import User
from app.domain.enums.platform_role_enum import PlatformRoleEnum

class IUserRepository(ABC):
    """
    Интерфейс репозитория для работы с пользователями платформы.

        Управляет CRUD операциями и атрибутами пользователя, включая роль, пароль и токен версии.

        Методы:
            * create — создаёт нового пользователя с логином, email и хэшом пароля
            * get_by_email — возвращает пользователя по email
            * get_by_id — возвращает пользователя по UUID
            * attach_secondary_email — добавляет вторичный email к пользователю
            * update_password — обновляет хэш пароля
            * update_role — изменяет роль пользователя (PlatformRoleEnum)
            * update_token_version — обновляет версию токенов пользователя (для ротации JWT)
    """

    @abstractmethod
    async def create(self, user: User) -> None:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        pass

    @abstractmethod
    async def attach_secondary_email(self, user_id: UUID, email: str) -> None:
        pass

    @abstractmethod
    async def update_password(self, user_id: UUID, password_hash: str) -> None:
        pass

    @abstractmethod
    async def update_role(self, user_id: UUID, role: PlatformRoleEnum) -> None:
        pass

    @abstractmethod
    async def update_token_version(self, user_id: UUID, version: int) -> None:
        pass