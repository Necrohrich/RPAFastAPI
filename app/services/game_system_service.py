#app/services/game_system_service.py
from uuid import UUID

from app.domain.entities import GameSystem
from app.domain.repositories import IGameSystemRepository
from app.dto import CreateGameSystemDTO, GameSystemResponseDTO, UpdateGameSystemDTO, PaginatedResponseDTO
from app.exceptions import GameSystemNotFoundException, GameSystemAlreadyExistsException, \
    GameSystemHasDependenciesException
from app.utils import Mapper
from app.validators import GameSystemValidator


class GameSystemService:
    """
        Application service responsible for game system management.

        Handles:
            - Creation and validation of game systems
            - Retrieval by ID, name, or paginated list
            - Updating game system fields
            - Deletion of game systems

        Responsibilities:
            - Uses IGameSystemRepository for data access
            - Validates name and description before write operations
            - Checks uniqueness of name before creation
            - Ensures existence before update or delete

        Does NOT:
            - Handle authentication or authorization
            - Manage games or characters directly
            - Contain infrastructure or persistence logic
    """
    def __init__(self, repo: IGameSystemRepository):
        self.repo = repo

    async def create(self, dto: CreateGameSystemDTO) -> GameSystemResponseDTO:
        GameSystemValidator.validate_name(dto.name)
        if dto.description is not None:
            GameSystemValidator.validate_description(dto.description)

        if await self.repo.get_by_name(dto.name):
            raise GameSystemAlreadyExistsException()

        game_system = Mapper.dto_to_entity(dto, GameSystem)
        response = await self.repo.create(game_system)
        return Mapper.entity_to_dto(response, GameSystemResponseDTO)

    async def get_by_id(self, game_system_id: UUID) -> GameSystemResponseDTO:
        game_system = await self.repo.get_by_id(game_system_id)
        if not game_system:
            raise GameSystemNotFoundException()
        return Mapper.entity_to_dto(game_system, GameSystemResponseDTO)

    #не используется
    async def get_by_name(self, name: str) -> GameSystemResponseDTO:
        game_system = await self.repo.get_by_name(name)
        if not game_system:
            raise GameSystemNotFoundException()
        return Mapper.entity_to_dto(game_system, GameSystemResponseDTO)

    async def get_all(self, page: int, page_size: int) -> PaginatedResponseDTO[GameSystemResponseDTO]:
        offset = (page - 1) * page_size
        items = await self.repo.get_all(offset=offset, limit=page_size)
        total = await self.repo.count_all()

        return PaginatedResponseDTO(
            items=[Mapper.entity_to_dto(item, GameSystemResponseDTO) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    async def get_all_list(self) -> list[GameSystemResponseDTO]:
        items = await self.repo.get_all(offset=0, limit=10000)
        return [Mapper.entity_to_dto(item, GameSystemResponseDTO) for item in items]

    async def update(self, game_system_id: UUID, dto: UpdateGameSystemDTO) -> GameSystemResponseDTO:
        if dto.name is not None:
            GameSystemValidator.validate_name(dto.name)
        if dto.description is not None:
            GameSystemValidator.validate_description(dto.description)

        game_system = await self.repo.get_by_id(game_system_id)
        if not game_system:
            raise GameSystemNotFoundException()

        if dto.name is not None:
            game_system.name = dto.name
        if dto.description is not None:
            game_system.description = dto.description

        response = await self.repo.update(game_system)
        return Mapper.entity_to_dto(response, GameSystemResponseDTO)

    async def delete(self, game_system_id: UUID) -> None:
        if not await self.repo.get_by_id(game_system_id):
            raise GameSystemNotFoundException()
        if await self.repo.has_dependencies(game_system_id):
            raise GameSystemHasDependenciesException()
        await self.repo.delete(game_system_id)

