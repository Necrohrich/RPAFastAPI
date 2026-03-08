#app/services/character_service.py
from uuid import UUID

from app.domain.entities import Character
from app.domain.repositories import ICharacterRepository, IGameSystemRepository, IUserRepository, IGameRepository
from app.dto import CreateCharacterDTO, CharacterResponseDTO, CharacterDetailResponseDTO, PaginatedResponseDTO, \
    UpdateCharacterDTO
from app.exceptions import GameSystemNotFoundException, NotFoundError, CharacterNotFoundException, \
    GameNotFoundException, CharacterPermissionException
from app.utils import Mapper
from app.validators import CharacterValidator


class CharacterService:
    """
        Application service responsible for character management.

        Handles:
            - Character creation with optional game system binding
            - Retrieval by ID (with and without relations), game, or author
            - Paginated character lists by game or user
            - Partial updates of character fields
            - Soft delete and restore of characters
            - Hard delete for administrative purposes

        Responsibilities:
            - Uses ICharacterRepository as primary data source
            - Uses IGameSystemRepository to validate game_system_id on creation
            - Uses IGameRepository to validate game existence before listing characters
            - Validates character name via CharacterValidator
            - Enforces ownership check on update and soft_delete (requester_id == author)
            - Injects author_id from caller context, not from DTO

        Does NOT:
            - Handle authentication or token validation
            - Enforce admin-level access for restore and delete (delegated to router/Discord layer)
            - Manage game membership or join requests
            - Contain infrastructure or persistence logic
    """

    def __init__(
            self,
            repo: ICharacterRepository,
            game_system_repo: IGameSystemRepository,
            user_repo: IUserRepository,
            game_repo: IGameRepository
    ):
        self.repo = repo
        self.game_system_repo = game_system_repo
        self.user_repo=user_repo
        self.game_repo=game_repo

    async def create(self, dto: CreateCharacterDTO, author_id: UUID)  -> CharacterResponseDTO:
        CharacterValidator.validate_name(dto.name)
        if dto.game_system_id is not None:
            if not await self.game_system_repo.get_by_id(dto.game_system_id):
                raise GameSystemNotFoundException()

        data = dto.model_dump()
        data["user_id"] = author_id
        character = Mapper.dto_to_entity(data, Character)
        response = await self.repo.create(character)
        return Mapper.entity_to_dto(response, CharacterResponseDTO)

    async def get_by_id(self, character_id: UUID) -> CharacterResponseDTO:
        character = await self.repo.get_by_id(character_id)
        if not character:
            raise CharacterNotFoundException()
        return Mapper.entity_to_dto(character, CharacterResponseDTO)

    async def get_by_id_with_relations(self, character_id: UUID) -> CharacterDetailResponseDTO:
        character = await self.repo.get_by_id_with_relations(character_id)
        if not character:
            raise CharacterNotFoundException()
        return Mapper.entity_to_dto(character, CharacterDetailResponseDTO)

    async def get_by_game_id(self, game_id: UUID, page: int, page_size: int) -> PaginatedResponseDTO[CharacterResponseDTO]:
        if not await self.game_repo.get_by_id(game_id):
            raise GameNotFoundException()
        offset = (page - 1) * page_size
        items = await self.repo.get_by_game_id(game_id=game_id, offset=offset, limit=page_size)
        total = await self.repo.count_by_game_id(game_id)

        return PaginatedResponseDTO(
            items=[Mapper.entity_to_dto(item, CharacterResponseDTO) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    async def get_by_user_id(self, author_id: UUID, page: int, page_size: int) -> PaginatedResponseDTO[CharacterResponseDTO]:
        if not await self.user_repo.get_by_id(author_id):
            raise NotFoundError()
        offset = (page - 1) * page_size
        items = await self.repo.get_by_user_id(user_id=author_id, offset=offset, limit=page_size)
        total = await self.repo.count_by_user_id(author_id)

        return PaginatedResponseDTO(
            items=[Mapper.entity_to_dto(item, CharacterResponseDTO) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    async def update(self, dto: UpdateCharacterDTO, requester_id: UUID) -> CharacterResponseDTO:
        if dto.name is not None:
            CharacterValidator.validate_name(dto.name)

        character = await self.repo.get_by_id(dto.id)
        if not character:
            raise CharacterNotFoundException()

        if character.user_id != requester_id:
            raise CharacterPermissionException()

        if dto.name is not None:
            character.name = dto.name
        if dto.avatar is not None:
            character.avatar = dto.avatar
        if dto.sheet_data is not None:
            character.sheet_data = dto.sheet_data

        response = await self.repo.update(character)
        return Mapper.entity_to_dto(response, CharacterResponseDTO)


    async def soft_delete(self, character_id: UUID, requester_id: UUID) -> None:
        character = await self.repo.get_by_id(character_id)
        if not character:
            raise CharacterNotFoundException()

        if character.user_id != requester_id:
            raise CharacterPermissionException()

        await self.repo.soft_delete(character_id)

    async def restore(self, character_id: UUID) -> None:
        await self.repo.restore(character_id)

    async def delete(self, character_id: UUID) -> None:
        if not await self.repo.get_by_id(character_id):
            raise CharacterNotFoundException()
        await self.repo.delete(character_id)


