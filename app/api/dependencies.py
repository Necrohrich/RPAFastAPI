#app/api/dependencies.py
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.database import get_uow, UnitOfWork
from app.infrastructure.repositories import DiscordRepository, TokenRepository, UserRepository, CharacterRepository, \
    GameSystemRepository, GameRepository, GameSessionRepository, GameReviewRepository
from app.services import (AuthService, UserService, GameService, CharacterService, GameSystemService,
                          GameSessionService, GameReviewService)
from app.dto.auth_dtos import UserDTO

security = HTTPBearer()

# ────────────────────────────────────────────────────────────
# Session
# ────────────────────────────────────────────────────────────

async def get_session(uow: UnitOfWork = Depends(get_uow)):
    return uow.session


# ────────────────────────────────────────────────────────────
# Repositories
# ────────────────────────────────────────────────────────────

def get_user_repo(session: AsyncSession = Depends(get_session)):
    return UserRepository(session)

def get_token_repo(session: AsyncSession = Depends(get_session)):
    return TokenRepository(session)

def get_discord_repo(session: AsyncSession = Depends(get_session)):
    return DiscordRepository(session)

def get_game_repo(session: AsyncSession = Depends(get_session)):
    return GameRepository(session)

def get_game_system_repo(session: AsyncSession = Depends(get_session)):
    return GameSystemRepository(session)

def get_character_repo(session: AsyncSession = Depends(get_session)):
    return CharacterRepository(session)

def get_game_session_repo(session: AsyncSession = Depends(get_session)):
    return GameSessionRepository(session)

def get_game_review_repo(session: AsyncSession = Depends(get_session)):
    return GameReviewRepository(session)

# ────────────────────────────────────────────────────────────
# Services
# ────────────────────────────────────────────────────────────

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

def get_game_system_service(
        repo=Depends(get_game_system_repo),
):
    return GameSystemService(repo)

def get_character_service(
        repo=Depends(get_character_repo),
        game_system_repo=Depends(get_game_system_repo),
        user_repo=Depends(get_user_repo),
        game_repo=Depends(get_game_repo),
        discord_repo=Depends(get_discord_repo)
):
    return CharacterService(repo, game_system_repo, user_repo, game_repo, discord_repo)

def get_game_service(
        repo=Depends(get_game_repo),
        character_repo=Depends(get_character_repo),
        game_system_repo=Depends(get_game_system_repo),
        user_repo=Depends(get_user_repo),
        discord_repo=Depends(get_discord_repo)
):
    return GameService(repo, character_repo, game_system_repo, user_repo, discord_repo)

def get_game_session_service(
        repo=Depends(get_game_session_repo),
        game_repo=Depends(get_game_repo),
        review_repo=Depends(get_game_review_repo),
):
    return GameSessionService(repo, game_repo, review_repo=review_repo)

def get_game_review_service(
        repo=Depends(get_game_review_repo),
        session_repo=Depends(get_game_session_repo),
        game_repo=Depends(get_game_repo),
        user_repo=Depends(get_user_repo),
):
    return GameReviewService(repo, session_repo, game_repo, user_repo)

# ────────────────────────────────────────────────────────────
# Current user
# ────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AuthService = Depends(get_auth_service),
) -> UserDTO:
    token = credentials.credentials
    return await service.get_current_user(token)