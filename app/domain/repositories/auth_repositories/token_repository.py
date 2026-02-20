#app/domain/repositories/auth_repositories/token_repository.py
from abc import ABC
from datetime import datetime
from uuid import UUID

class ITokenRepository(ABC):

    async def create(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime
    ) -> None:
        pass

    async def get(self, token_hash: str):
        pass

    async def revoke(self, token_hash: str) -> None:
        pass

    async def revoke_all(self, user_id: UUID) -> None:
        pass

    async def delete_expired(self) -> None:
        pass