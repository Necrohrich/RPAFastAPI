#app/discord/dependencies.py
from contextlib import asynccontextmanager

from app.infrastructure.db.database import UnitOfWork
from app.infrastructure.repositories.auth_repositories.discord_repository import DiscordRepository
from app.infrastructure.repositories.auth_repositories.token_repository import TokenRepository
from app.infrastructure.repositories.auth_repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService

@asynccontextmanager
async def auth_service_ctx():
    async with UnitOfWork() as uow:
        user_repo = UserRepository(uow.session)
        token_repo = TokenRepository(uow.session)
        yield AuthService(user_repo, token_repo)

@asynccontextmanager
async def user_service_ctx():
    async with UnitOfWork() as uow:
        user_repo = UserRepository(uow.session)
        discord_repo = DiscordRepository(uow.session)
        yield UserService(user_repo, discord_repo)