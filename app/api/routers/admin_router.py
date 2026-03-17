# app/api/routers/admin_router.py

from fastapi import APIRouter, Depends, status
from uuid import UUID

from app.api.security import require_superadmin, require_support, require_moderator
from app.domain.enums.platform_role_enum import PlatformRoleEnum
from app.dto import GameSystemResponseDTO, CreateGameSystemDTO, PaginatedResponseDTO, UpdateGameSystemDTO, \
    GameSessionResponseDTO
from app.services import GameSystemService, CharacterService, GameService, GameSessionService
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.api.dependencies import get_user_service, get_auth_service, get_game_system_service, get_character_service, \
    get_game_service, get_game_session_service
from app.dto.auth_dtos import UserDTO

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

# ────────────────────────────────────────────────────────────
# Auth
# ────────────────────────────────────────────────────────────

@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_superadmin)]
)
async def logout_all(
        user_id: UUID,
        service: AuthService = Depends(get_auth_service),
):
    await service.logout_all(user_id)


# ────────────────────────────────────────────────────────────
# Users
# ────────────────────────────────────────────────────────────

@router.put(
    "/{user_id}/role",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_superadmin)]
)
async def update_role(
        user_id: UUID,
        role: PlatformRoleEnum,
        service: UserService = Depends(get_user_service),
):
    await service.update_role(user_id, role)


@router.get(
    "/discord/{discord_id}",
    response_model=UserDTO,
    dependencies=[Depends(require_support)]
)
async def get_user_by_discord(
        discord_id: int,
        service: UserService = Depends(get_user_service),
):
    return await service.get_user_by_discord(discord_id)


# ────────────────────────────────────────────────────────────
# Game Systems
# ────────────────────────────────────────────────────────────

@router.post(
    "/game-systems",
    response_model=GameSystemResponseDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_superadmin)]
)
async def create_game_system(
        dto: CreateGameSystemDTO,
        service: GameSystemService = Depends(get_game_system_service),
):
    return await service.create(dto)


@router.get(
    "/game-systems",
    response_model=PaginatedResponseDTO[GameSystemResponseDTO],
    dependencies=[Depends(require_support)]
)
async def get_all_game_systems(
        page: int = 1,
        page_size: int = 20,
        service: GameSystemService = Depends(get_game_system_service),
):
    return await service.get_all(page=page, page_size=page_size)


@router.get(
    "/game-systems/{game_system_id}",
    response_model=GameSystemResponseDTO,
    dependencies=[Depends(require_support)]
)
async def get_game_system_by_id(
        game_system_id: UUID,
        service: GameSystemService = Depends(get_game_system_service),
):
    return await service.get_by_id(game_system_id)


@router.patch(
    "/game-systems/{game_system_id}",
    response_model=GameSystemResponseDTO,
    dependencies=[Depends(require_superadmin)]
)
async def update_game_system(
        game_system_id: UUID,
        dto: UpdateGameSystemDTO,
        service: GameSystemService = Depends(get_game_system_service),
):
    return await service.update(game_system_id, dto)


@router.delete(
    "/game-systems/{game_system_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_superadmin)]
)
async def delete_game_system(
        game_system_id: UUID,
        service: GameSystemService = Depends(get_game_system_service),
):
    await service.delete(game_system_id)

# ────────────────────────────────────────────────────────────
# Characters
# ────────────────────────────────────────────────────────────

@router.post(
    "/characters/{character_id}/restore",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_moderator)]
)
async def restore_character(
        character_id: UUID,
        service: CharacterService = Depends(get_character_service),
):
    await service.restore(character_id)


@router.delete(
    "/characters/{character_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_superadmin)]
)
async def delete_character(
        character_id: UUID,
        service: CharacterService = Depends(get_character_service),
):
    await service.delete(character_id)

# ────────────────────────────────────────────────────────────
# Games
# ────────────────────────────────────────────────────────────

@router.post(
    "/games/{game_id}/restore",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_moderator)]
)
async def restore_game(
        game_id: UUID,
        service: GameService = Depends(get_game_service),
):
    await service.restore(game_id)


@router.delete(
    "/games/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_superadmin)]
)
async def delete_game(
        game_id: UUID,
        service: GameService = Depends(get_game_service),
):
    await service.delete(game_id)


# ────────────────────────────────────────────────────────────
# Game Sessions
# ────────────────────────────────────────────────────────────

@router.post(
    "/game-sessions/{session_id}/invalidate",
    response_model=GameSessionResponseDTO,
    dependencies=[Depends(require_moderator)],
)
async def invalidate_game_session(
        session_id: UUID,
        service: GameSessionService = Depends(get_game_session_service),
):
    return await service.invalidate(session_id)