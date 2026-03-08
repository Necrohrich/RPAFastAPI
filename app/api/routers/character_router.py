#app/api/routers/character_router.py
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_character_service
from app.dto import CharacterResponseDTO, CreateCharacterDTO, UserDTO, CharacterDetailResponseDTO, \
    UpdateCharacterDTO
from app.services import CharacterService

router = APIRouter(
    prefix="/characters",
    tags=["Characters"],
)

@router.post(
    "",
    response_model=CharacterResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_character(
        dto: CreateCharacterDTO,
        current_user: UserDTO = Depends(get_current_user),
        service: CharacterService = Depends(get_character_service),
):
    return await service.create(dto, author_id=current_user.id)

@router.get(
    "/{character_id}",
    response_model=CharacterDetailResponseDTO,
)
async def get_character(
        character_id: UUID,
        service: CharacterService = Depends(get_character_service),
):
    return await service.get_by_id_with_relations(character_id)


@router.patch(
    "/{character_id}",
    response_model=CharacterResponseDTO,
)
async def update_character(
        character_id: UUID,
        dto: UpdateCharacterDTO,
        current_user: UserDTO = Depends(get_current_user),
        service: CharacterService = Depends(get_character_service),
):
    return await service.update(character_id, dto, requester_id=current_user.id)


@router.delete(
    "/{character_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def soft_delete_character(
        character_id: UUID,
        current_user: UserDTO = Depends(get_current_user),
        service: CharacterService = Depends(get_character_service),
):
    await service.soft_delete(character_id, requester_id=current_user.id)