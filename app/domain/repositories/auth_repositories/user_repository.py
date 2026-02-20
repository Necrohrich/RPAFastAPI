#app/domain/repositories/auth_repositories/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.user import User
from app.domain.enums.platform_role_enum import PlatformRoleEnum

class IUserRepository(ABC):

    @abstractmethod
    async def create(self, login:str, email: str, password_hash: str) -> User:
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