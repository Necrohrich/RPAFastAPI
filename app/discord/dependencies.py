#app/discord/dependencies.py
from contextlib import asynccontextmanager

from app.infrastructure.db.database import UnitOfWork
from app.infrastructure.repositories import DiscordRepository, TokenRepository, UserRepository, GameSystemRepository, \
    CharacterRepository, GameRepository, GameSessionRepository
from app.services import AuthService, UserService, GameSystemService, GameService, CharacterService, GameSessionService


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

@asynccontextmanager
async def character_service_ctx():
    async with UnitOfWork() as uow:
        character_repo = CharacterRepository(uow.session)
        game_system_repo = GameSystemRepository(uow.session)
        user_repo = UserRepository(uow.session)
        game_repo = GameRepository(uow.session)
        discord_repo = DiscordRepository(uow.session)
        yield CharacterService(character_repo, game_system_repo, user_repo, game_repo, discord_repo)

@asynccontextmanager
async def game_service_ctx():
    async with UnitOfWork() as uow:
        game_repo = GameRepository(uow.session)
        character_repo = CharacterRepository(uow.session)
        game_system_repo = GameSystemRepository(uow.session)
        user_repo = UserRepository(uow.session)
        yield GameService(game_repo, character_repo, game_system_repo, user_repo)

@asynccontextmanager
async def game_system_service_ctx():
    async with UnitOfWork() as uow:
        game_system_repo = GameSystemRepository(uow.session)
        yield GameSystemService(game_system_repo)

@asynccontextmanager
async def game_session_service_ctx():
    async with UnitOfWork() as uow:
        game_session_repo = GameSessionRepository(uow.session)
        game_repo = GameRepository(uow.session)
        yield GameSessionService(game_session_repo, game_repo)