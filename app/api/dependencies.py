#app/api/dependencies.py
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.database import get_uow, UnitOfWork
from app.infrastructure.repositories import DiscordRepository, TokenRepository, UserRepository
from app.services import AuthService, UserService
from app.dto.auth_dtos import UserDTO

security = HTTPBearer()

async def get_session(uow: UnitOfWork = Depends(get_uow)):
    return uow.session

def get_user_repo(session: AsyncSession = Depends(get_session)):
    return UserRepository(session)


def get_token_repo(session: AsyncSession = Depends(get_session)):
    return TokenRepository(session)


def get_discord_repo(session: AsyncSession = Depends(get_session)):
    return DiscordRepository(session)


def get_auth_service(
        user_repo=Depends(get_user_repo),
        token_repo=Depends(get_token_repo),
):
    return AuthService(user_repo, token_repo)


def get_user_service(
        user_repo=Depends(get_user_repo),
        discord_repo=Depends(get_discord_repo),
):
    return UserService(user_repo, discord_repo)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AuthService = Depends(get_auth_service),
) -> UserDTO:
    token = credentials.credentials

    return await service.get_current_user(token)