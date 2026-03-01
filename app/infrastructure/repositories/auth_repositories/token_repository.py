#app/infrastructure/repositories/auth_repositories/token_repository.py
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional
from app.domain.entities.refresh_token import RefreshToken
from app.domain.repositories.auth_repositories.token_repository import ITokenRepository
from app.infrastructure.models import RefreshTokenModel
from app.utils.mapper import Mapper


class TokenRepository(ITokenRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, token: RefreshToken) -> None:
        model = Mapper.entity_to_model(token, RefreshTokenModel)
        self.session.add(model)

    async def get(self, token_hash: str) -> Optional[RefreshToken]:
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash == token_hash
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return Mapper.model_to_entity(model, RefreshToken)

    async def revoke(self, token_hash: str) -> None:
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash == token_hash
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.revoked_at = datetime.now(timezone.utc)

    async def revoke_all(self, user_id: UUID) -> None:
        stmt = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked_at.is_(None)
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)

    async def delete_expired(self) -> None:
        stmt = delete(RefreshTokenModel).where(
            RefreshTokenModel.expires_at <= datetime.now(timezone.utc)
        )

        await self.session.execute(stmt)