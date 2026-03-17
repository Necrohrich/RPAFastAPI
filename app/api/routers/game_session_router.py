# app/api/routers/game_session_router.py
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_game_session_service
from app.dto import PaginatedResponseDTO, GameSessionResponseDTO, CreateGameSessionDTO, UpdateGameSessionDTO
from app.dto.auth_dtos import UserDTO
from app.services import GameSessionService

router = APIRouter(
    prefix="/game-sessions",
    tags=["Game Sessions"],
)

# ────────────────────────────────────────────────────────────
# CRUD
# ────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=GameSessionResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_game_session(
        dto: CreateGameSessionDTO,
        _: UserDTO = Depends(get_current_user),
        service: GameSessionService = Depends(get_game_session_service),
):
    return await service.create(dto)


@router.get(
    "/{session_id}",
    response_model=GameSessionResponseDTO,
)
async def get_game_session(
        session_id: UUID,
        service: GameSessionService = Depends(get_game_session_service),
):
    return await service.get_by_id(session_id)


@router.get(
    "",
    response_model=PaginatedResponseDTO[GameSessionResponseDTO],
)
async def get_sessions_by_game(
        game_id: UUID,
        page: int = 1,
        page_size: int = 20,
        service: GameSessionService = Depends(get_game_session_service),
):
    return await service.get_by_game_id(game_id, page=page, page_size=page_size)


@router.get(
    "/games/{game_id}/active",
    response_model=GameSessionResponseDTO,
)
async def get_active_session(
        game_id: UUID,
        service: GameSessionService = Depends(get_game_session_service),
):
    return await service.get_active_by_game_id(game_id)


@router.patch(
    "/{session_id}",
    response_model=GameSessionResponseDTO,
)
async def update_game_session(
        session_id: UUID,
        dto: UpdateGameSessionDTO,
        _: UserDTO = Depends(get_current_user),
        service: GameSessionService = Depends(get_game_session_service),
):
    return await service.update(session_id, dto)


# ────────────────────────────────────────────────────────────
# Status transitions
# ────────────────────────────────────────────────────────────

@router.post(
    "/{session_id}/start",
    response_model=GameSessionResponseDTO,
)
async def start_session(
        session_id: UUID,
        _: UserDTO = Depends(get_current_user),
        service: GameSessionService = Depends(get_game_session_service),
):
    return await service.start(session_id)


@router.post(
    "/{session_id}/complete",
    response_model=GameSessionResponseDTO,
)
async def complete_session(
        session_id: UUID,
        _: UserDTO = Depends(get_current_user),
        service: GameSessionService = Depends(get_game_session_service),
):
    return await service.complete(session_id)


@router.post(
    "/{session_id}/cancel",
    response_model=GameSessionResponseDTO,
)
async def cancel_session(
        session_id: UUID,
        _: UserDTO = Depends(get_current_user),
        service: GameSessionService = Depends(get_game_session_service),
):
    return await service.cancel(session_id)