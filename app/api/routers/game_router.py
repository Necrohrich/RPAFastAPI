# app/api/routers/game_router.py
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_game_service
from app.domain.enums import PlayerStatusEnum
from app.dto import (
    CreateGameDTO, GameResponseDTO, GameDetailedResponseDTO,
    PaginatedResponseDTO, GamePlayerResponseDTO, UpdateGameDTO, CharacterResponseDTO
)
from app.dto.auth_dtos import UserDTO
from app.services import GameService

router = APIRouter(
    prefix="/games",
    tags=["Games"],
)

# ────────────────────────────────────────────────────────────
# Games CRUD
# ────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=GameResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_game(
        dto: CreateGameDTO,
        current_user: UserDTO = Depends(get_current_user),
        service: GameService = Depends(get_game_service),
):
    return await service.create(dto, author_id=current_user.id)


@router.get(
    "/{game_id}",
    response_model=GameDetailedResponseDTO,
)
async def get_game(
        game_id: UUID,
        service: GameService = Depends(get_game_service),
):
    return await service.get_by_id_with_relations(game_id)


@router.get(
    "",
    response_model=PaginatedResponseDTO[GameResponseDTO],
)
async def get_games_by_author(
        author_id: UUID,
        page: int = 1,
        page_size: int = 20,
        service: GameService = Depends(get_game_service),
):
    return await service.get_by_author_id(author_id, page=page, page_size=page_size)


@router.patch(
    "/{game_id}",
    response_model=GameResponseDTO,
)
async def update_game(
        game_id: UUID,
        dto: UpdateGameDTO,
        current_user: UserDTO = Depends(get_current_user),
        service: GameService = Depends(get_game_service),
):
    return await service.update(game_id, dto, requester_id=current_user.id)


@router.delete(
    "/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def soft_delete_game(
        game_id: UUID,
        current_user: UserDTO = Depends(get_current_user),
        service: GameService = Depends(get_game_service),
):
    await service.soft_delete(game_id, requester_id=current_user.id)


# ────────────────────────────────────────────────────────────
# Players
# ────────────────────────────────────────────────────────────

@router.get(
    "/{game_id}/players",
    response_model=PaginatedResponseDTO[GamePlayerResponseDTO],
)
async def get_players(
        game_id: UUID,
        page: int = 1,
        page_size: int = 20,
        player_status: Optional[PlayerStatusEnum] = None,
        service: GameService = Depends(get_game_service),
):
    return await service.get_players(game_id, page=page, page_size=page_size, status=player_status)


@router.post(
    "/{game_id}/players/join",
    response_model=GamePlayerResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def request_join(
        game_id: UUID,
        current_user: UserDTO = Depends(get_current_user),
        service: GameService = Depends(get_game_service),
):
    return await service.request_join(game_id, user_id=current_user.id)


@router.post(
    "/{game_id}/players/{player_id}/approve",
    response_model=GamePlayerResponseDTO,
)
async def approve_join(
        game_id: UUID,
        player_id: UUID,
        current_user: UserDTO = Depends(get_current_user),
        service: GameService = Depends(get_game_service),
):
    return await service.approve_join(game_id, player_id, requester_id=current_user.id)


@router.post(
    "/{game_id}/players/{player_id}/reject",
    response_model=GamePlayerResponseDTO,
)
async def reject_join(
        game_id: UUID,
        player_id: UUID,
        current_user: UserDTO = Depends(get_current_user),
        service: GameService = Depends(get_game_service),
):
    return await service.reject_join(game_id, player_id, requester_id=current_user.id)


@router.delete(
    "/{game_id}/players/{player_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_player(
        game_id: UUID,
        player_id: UUID,
        current_user: UserDTO = Depends(get_current_user),
        service: GameService = Depends(get_game_service),
):
    await service.remove_player(game_id, player_id, requester_id=current_user.id)


# ────────────────────────────────────────────────────────────
# Characters in game
# ────────────────────────────────────────────────────────────

@router.post(
    "/{game_id}/characters/{character_id}",
    response_model=CharacterResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def attach_character(
        game_id: UUID,
        character_id: UUID,
        current_user: UserDTO = Depends(get_current_user),
        service: GameService = Depends(get_game_service),
):
    return await service.attach_character(game_id, character_id, requester_id=current_user.id)


@router.delete(
    "/{game_id}/characters/{character_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def detach_character(
        game_id: UUID,
        character_id: UUID,
        current_user: UserDTO = Depends(get_current_user),
        service: GameService = Depends(get_game_service),
):
    await service.detach_character(game_id, character_id, requester_id=current_user.id)