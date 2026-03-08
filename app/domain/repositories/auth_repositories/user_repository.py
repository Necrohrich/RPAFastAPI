#app/domain/repositories/auth_repositories/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities import Character, Game, User
from app.domain.enums import PlatformRoleEnum

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
        * get_my_games — возвращает paginated список игр созданных пользователем
        * count_my_games — возвращает количество игр созданных пользователем
        * get_participated_games — возвращает paginated список игр где пользователь участник
        * count_participated_games — возвращает количество игр где пользователь участник
        * get_my_characters — возвращает paginated список персонажей пользователя
        * count_my_characters — возвращает количество персонажей пользователя
    """

    @abstractmethod
    async def create(self, user: User) -> None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]: ...

    @abstractmethod
    async def attach_secondary_email(self, user_id: UUID, email: str) -> None: ...

    @abstractmethod
    async def update_password(self, user_id: UUID, password_hash: str) -> None: ...

    @abstractmethod
    async def update_role(self, user_id: UUID, role: PlatformRoleEnum) -> None: ...

    @abstractmethod
    async def update_token_version(self, user_id: UUID, version: int) -> None: ...

    @abstractmethod
    async def get_my_games(self, user_id: UUID, offset: int, limit: int) -> list[Game]: ...

    @abstractmethod
    async def count_my_games(self, user_id: UUID) -> int: ...

    @abstractmethod
    async def get_participated_games(self, user_id: UUID, offset: int, limit: int) -> list[Game]: ...

    @abstractmethod
    async def count_participated_games(self, user_id: UUID) -> int: ...

    @abstractmethod
    async def get_my_characters(self, user_id: UUID, offset: int, limit: int) -> list[Character]: ...

    @abstractmethod
    async def count_my_characters(self, user_id: UUID) -> int: ...