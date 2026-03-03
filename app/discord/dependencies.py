#app/discord/dependencies.py
from app.infrastructure.db.database import UnitOfWork
from app.infrastructure.repositories.auth_repositories.discord_repository import DiscordRepository
from app.infrastructure.repositories.auth_repositories.token_repository import TokenRepository
from app.infrastructure.repositories.auth_repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService


async def get_auth_service():
    async with UnitOfWork() as uow:
        user_repo = UserRepository(uow.session)
        token_repo = TokenRepository(uow.session)
        return AuthService(user_repo, token_repo)

async def get_user_service():
    async with UnitOfWork() as uow:
        user_repo = UserRepository(uow.session)
        discord_repo = DiscordRepository(uow.session)
        return UserService(user_repo, discord_repo)