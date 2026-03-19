# app/api/routers/user_router.py
from typing import Optional

from fastapi import APIRouter, Depends, status

from app.domain.enums import ReviewStatusEnum
from app.services import GameReviewService
from app.services.user_service import UserService
from app.api.dependencies import get_user_service, get_current_user, get_game_review_service
from app.dto import PaginatedResponseDTO, GameResponseDTO, CharacterResponseDTO, GameReviewResponseDTO
from app.dto.auth_dtos import UserDTO, ChangePasswordDTO, DiscordDTO, SecondaryEmailDTO

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.get("/me", response_model=UserDTO)
async def get_me(
    current_user: UserDTO = Depends(get_current_user),
):
    return current_user


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    dto: ChangePasswordDTO,
    current_user: UserDTO = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    await service.change_password(current_user.id, dto)


@router.patch("/me/secondary-email", status_code=status.HTTP_204_NO_CONTENT)
async def attach_secondary_email(
    dto: SecondaryEmailDTO,
    current_user: UserDTO = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    await service.attach_secondary_email(user_id=current_user.id, email=dto.email)


@router.patch("/me/primary-discord-id", status_code=status.HTTP_204_NO_CONTENT)
async def attach_primary_discord_id(
    dto: DiscordDTO,
    current_user: UserDTO = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    await service.attach_primary_discord_id(user_id=current_user.id, discord_id=dto.discord_id)


# @router.patch("/me/secondary-discord-id", status_code=status.HTTP_204_NO_CONTENT)
# async def attach_secondary_discord_id(
#     dto: DiscordDTO,
#     current_user: UserDTO = Depends(get_current_user),
#     service: UserService = Depends(get_user_service),
# ):
#     await service.attach_secondary_discord_id(user_id=current_user.id, discord_id=dto.discord_id)


# ────────────────────────────────────────────────────────────
# Мои игры
# ────────────────────────────────────────────────────────────

@router.get("/me/games", response_model=PaginatedResponseDTO[GameResponseDTO])
async def get_my_games(
    page: int = 1,
    page_size: int = 20,
    current_user: UserDTO = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await service.get_my_games(current_user.id, page=page, page_size=page_size)


@router.get("/me/games/participated", response_model=PaginatedResponseDTO[GameResponseDTO])
async def get_participated_games(
    page: int = 1,
    page_size: int = 20,
    current_user: UserDTO = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await service.get_participated_games(current_user.id, page=page, page_size=page_size)


# ────────────────────────────────────────────────────────────
# Мои персонажи
# ────────────────────────────────────────────────────────────

@router.get("/me/characters", response_model=PaginatedResponseDTO[CharacterResponseDTO])
async def get_my_characters(
    page: int = 1,
    page_size: int = 20,
    current_user: UserDTO = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await service.get_my_characters(current_user.id, page=page, page_size=page_size)

# ────────────────────────────────────────────────────────────
# Мои отзывы
# ────────────────────────────────────────────────────────────

@router.get(
    "/me/reviews",
    response_model=PaginatedResponseDTO[GameReviewResponseDTO],
)
async def get_my_reviews(
        page: int = 1,
        page_size: int = 20,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        current_user: UserDTO = Depends(get_current_user),
        service: GameReviewService = Depends(get_game_review_service),
):
    """Отзывы текущего пользователя. По умолчанию только SEND."""
    return await service.get_by_user_id(
        current_user.id,
        page=page,
        page_size=page_size,
        statuses=statuses,
    )