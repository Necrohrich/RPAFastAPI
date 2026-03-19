# app/api/routers/game_review_router.py
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_game_review_service
from app.dto import (
    PaginatedResponseDTO,
    GameReviewResponseDTO,
    UpdateGameReviewDTO,
    SendGameReviewDTO,
    CreateGameReviewDTO,
)
from app.dto.auth_dtos import UserDTO
from app.services.game_review_service import GameReviewService

router = APIRouter(
    prefix="/game-reviews",
    tags=["Game Reviews"],
)

# ────────────────────────────────────────────────────────────
# CRUD
# ────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=GameReviewResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
        game_id: UUID,
        session_id: UUID,
        current_user: UserDTO = Depends(get_current_user),
        service: GameReviewService = Depends(get_game_review_service),
):
    """
    Создаёт отзыв для текущего пользователя.
    Проверяет: принятый игрок, не автор, присутствовал на сессии, дубликат.
    """
    dto = CreateGameReviewDTO(
        game_id=game_id,
        session_id=session_id,
        user_id=current_user.id,
    )
    return await service.create(dto)


@router.get(
    "/{review_id}",
    response_model=GameReviewResponseDTO,
)
async def get_review(
        review_id: UUID,
        service: GameReviewService = Depends(get_game_review_service),
):
    return await service.get_by_id(review_id)


@router.patch(
    "/{review_id}",
    response_model=GameReviewResponseDTO,
)
async def update_review(
        review_id: UUID,
        dto: UpdateGameReviewDTO,
        current_user: UserDTO = Depends(get_current_user),
        service: GameReviewService = Depends(get_game_review_service),
):
    """Обновляет поля отзыва. Доступно только пока статус CREATED."""
    return await service.update(review_id, dto, requester_id=current_user.id)


@router.post(
    "/{review_id}/send",
    response_model=GameReviewResponseDTO,
)
async def send_review(
        review_id: UUID,
        dto: SendGameReviewDTO,
        current_user: UserDTO = Depends(get_current_user),
        service: GameReviewService = Depends(get_game_review_service),
):
    """Отправляет отзыв (CREATED → SEND). Требует заполненных rating и comment."""
    return await service.send(review_id, dto, requester_id=current_user.id)


@router.post(
    "/{review_id}/cancel",
    response_model=GameReviewResponseDTO,
)
async def cancel_review(
        review_id: UUID,
        current_user: UserDTO = Depends(get_current_user),
        service: GameReviewService = Depends(get_game_review_service),
):
    """Отменяет отзыв (CREATED → CANCELED)."""
    return await service.cancel(review_id, requester_id=current_user.id)


# ────────────────────────────────────────────────────────────
# Выборки
# ────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedResponseDTO[GameReviewResponseDTO],
)
async def get_reviews_by_game(
        game_id: UUID,
        page: int = 1,
        page_size: int = 20,
        service: GameReviewService = Depends(get_game_review_service),
):
    """Список отзывов по игре (только SEND, без deleted)."""
    return await service.get_by_game_id(game_id, page=page, page_size=page_size)


@router.get(
    "/by-session/{session_id}",
    response_model=PaginatedResponseDTO[GameReviewResponseDTO],
)
async def get_reviews_by_session(
        session_id: UUID,
        page: int = 1,
        page_size: int = 20,
        service: GameReviewService = Depends(get_game_review_service),
):
    """Список отзывов по сессии (только SEND, без deleted)."""
    return await service.get_by_session_id(session_id, page=page, page_size=page_size)