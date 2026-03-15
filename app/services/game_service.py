#app/services/game_service.py
from typing import Optional
from uuid import UUID

from app.domain.entities import Game, GamePlayer
from app.domain.enums import PlayerStatusEnum
from app.domain.repositories import IUserRepository, IGameSystemRepository, ICharacterRepository, IGameRepository
from app.dto import CreateGameDTO, GameResponseDTO, GameDetailedResponseDTO, PaginatedResponseDTO, \
    GamePlayerResponseDTO, UpdateGameDTO, CharacterResponseDTO
from app.exceptions import GameSystemNotFoundException, GameAlreadyExistsException, GameNotFoundException, \
    NotFoundError, NotGameAuthorException, PlayerAlreadyInGameException, PlayerNotFoundException, \
    CharacterNotFoundException, CharacterPermissionException, CharacterAlreadyExistsException, \
    CharacterGameSystemMismatchException
from app.utils import Mapper
from app.validators import GameValidator


class GameService:
    """
        Application service responsible for game management and player participation.

        Handles:
            - Game creation, updating, soft delete, restore and hard delete
            - Retrieval of games by ID, author, with or without relations
            - Player join requests, approval, rejection and removal
            - Attaching and detaching characters to/from a game

        Responsibilities:
            - Uses IGameRepository as primary data source
            - Uses ICharacterRepository to manage character-game bindings
            - Uses IGameSystemRepository to validate game_system_id
            - Uses IUserRepository to verify user existence
            - Validates game name and Discord IDs via GameValidator
            - Enforces ownership check for update, soft_delete, approve, reject, remove_player
            - Enforces game_system compatibility when attaching characters
            - Limits regular players to one character per game, authors have no limit

        Does NOT:
            - Handle authentication or token validation
            - Enforce admin-level access for restore and delete (delegated to router/Discord layer)
            - Manage character CRUD outside of game binding
            - Contain infrastructure or persistence logic
        """
    def __init__(
            self,
            repo: IGameRepository,
            character_repo: ICharacterRepository,
            game_system_repo: IGameSystemRepository,
            user_repo: IUserRepository,
    ):
        self.repo = repo
        self.character_repo = character_repo
        self.user_repo=user_repo
        self.game_system_repo=game_system_repo

    async def _to_dto(self, game: Game) -> GameResponseDTO:
        dto = Mapper.entity_to_dto(game, GameResponseDTO)
        if game.game_system_id:
            game_system = await self.game_system_repo.get_by_id(game.game_system_id)
            dto.game_system_name = game_system.name if game_system else None
        return dto

    async def _enrich_list(self, games: list[Game]) -> list[GameResponseDTO]:
        system_ids = {g.game_system_id for g in games if g.game_system_id}
        systems = {sid: await self.game_system_repo.get_by_id(sid) for sid in system_ids}
        result = []
        for game in games:
            dto = Mapper.entity_to_dto(game, GameResponseDTO)
            system = systems.get(game.game_system_id)
            dto.game_system_name = system.name if system else None
            result.append(dto)
        return result

    async def create(self, dto: CreateGameDTO, author_id: UUID) -> GameResponseDTO:
        GameValidator.validate_name(dto.name)
        if not await self.game_system_repo.get_by_id(dto.game_system_id):
            raise GameSystemNotFoundException()
        GameValidator.validate_discord_id(dto.gm_id, dto.discord_role_id, dto.discord_main_channel_id)
        if await self.repo.get_by_name_and_author_id(author_id, dto.name) is not None:
            raise GameAlreadyExistsException()
        data = dto.model_dump()
        data["author_id"] = author_id
        game = Mapper.dto_to_entity(data, Game)
        response = await self.repo.create(game)
        return await self._to_dto(response)

    async def get_by_id(self, game_id: UUID) -> GameResponseDTO:
        game = await self.repo.get_by_id(game_id)
        if not game:
            raise GameNotFoundException()
        return await self._to_dto(game)

    async def get_by_id_with_relations(self, game_id: UUID) -> GameDetailedResponseDTO:
        game = await self.repo.get_by_id_with_relations(game_id)
        if not game:
            raise GameNotFoundException()
        return Mapper.entity_to_dto(game, GameDetailedResponseDTO)

    async def get_by_author_id(self, author_id: UUID, page: int, page_size: int) \
            -> PaginatedResponseDTO[GameResponseDTO]:
        if not await self.user_repo.get_by_id(author_id):
            raise NotFoundError()
        offset = (page - 1) * page_size
        items = await self.repo.get_by_author_id(author_id=author_id, offset=offset, limit=page_size)
        total = await self.repo.count_by_author_id(author_id)
        return PaginatedResponseDTO(
            items=await self._enrich_list(items),
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    async def get_players(self, game_id: UUID, page: int, page_size: int,
                          status: Optional[PlayerStatusEnum] = None) \
            -> PaginatedResponseDTO[GamePlayerResponseDTO]:
        if not await self.repo.get_by_id(game_id):
            raise GameNotFoundException()
        offset = (page - 1) * page_size
        items = await self.repo.get_players(game_id=game_id, offset=offset, limit=page_size, status=status)
        total = await self.repo.count_players(game_id, status=status)
        result = []
        for item in items:
            dto = Mapper.entity_to_dto(item, GamePlayerResponseDTO)
            user = await self.user_repo.get_by_id(item.user_id)
            dto.name = user.login if user else str(item.user_id)
            result.append(dto)
        return PaginatedResponseDTO(
            items=result,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    # только в Дискорд
    async def get_players_list(
            self, game_id: UUID, status: Optional[PlayerStatusEnum] = None
    ) -> list[GamePlayerResponseDTO]:
        if not await self.repo.get_by_id(game_id):
            raise GameNotFoundException()
        items = await self.repo.get_players(game_id=game_id, offset=0, limit=None, status=status)
        result = []
        for item in items:
            dto = Mapper.entity_to_dto(item, GamePlayerResponseDTO)
            user = await self.user_repo.get_by_id(item.user_id)
            dto.name = user.login if user else str(item.user_id)
            result.append(dto)
        return result

    async def update(self, game_id: UUID, dto: UpdateGameDTO, requester_id: UUID) -> GameResponseDTO:
        if dto.name is not None:
            GameValidator.validate_name(dto.name)
        GameValidator.validate_discord_id(dto.gm_id, dto.discord_role_id, dto.discord_main_channel_id)
        game = await self.repo.get_by_id(game_id)
        if not game:
            raise GameNotFoundException()
        if game.author_id != requester_id:
            raise NotGameAuthorException()
        if dto.name is not None:
            game.name = dto.name
        if dto.game_system_id is not None:
            if not await self.game_system_repo.get_by_id(dto.game_system_id):
                raise GameSystemNotFoundException()
            game.game_system_id = dto.game_system_id
        if dto.gm_id is not None:
            game.gm_id = dto.gm_id
        if dto.discord_role_id is not None:
            game.discord_role_id = dto.discord_role_id
        if dto.discord_main_channel_id is not None:
            game.discord_main_channel_id = dto.discord_main_channel_id
        response = await self.repo.update(game)
        return await self._to_dto(response)

    async def soft_delete(self, game_id: UUID, requester_id) -> None:
        game = await self.repo.get_by_id(game_id)
        if not game:
            raise GameNotFoundException()
        if game.author_id != requester_id:
            raise NotGameAuthorException()
        await self.repo.soft_delete(game_id)

    async def restore(self, game_id: UUID) -> None:
        await self.repo.restore(game_id)

    async def delete(self, game_id: UUID) -> None:
        if not await self.repo.get_by_id(game_id):
            raise GameNotFoundException()
        await self.repo.delete(game_id)

    async def request_join(self, game_id: UUID, user_id: UUID) -> GamePlayerResponseDTO:
        if not await self.repo.get_by_id(game_id):
            raise GameNotFoundException()
        if not await self.user_repo.get_by_id(user_id):
            raise NotFoundError()
        if await self.repo.get_player(game_id, user_id):
            raise PlayerAlreadyInGameException()
        player = GamePlayer(
            game_id=game_id,
            user_id=user_id,
            status=PlayerStatusEnum.PENDING
        )
        response = await self.repo.add_player(player)
        return Mapper.entity_to_dto(response, GamePlayerResponseDTO)

    async def approve_join(self, game_id: UUID, player_id: UUID, requester_id: UUID) -> GamePlayerResponseDTO:
        game = await self.repo.get_by_id(game_id)
        if not game:
            raise GameNotFoundException()
        if game.author_id != requester_id:
            raise NotGameAuthorException()
        if not await self.repo.get_player(game_id, player_id):
            raise PlayerNotFoundException()
        response = await self.repo.update_player_status(game_id, player_id, PlayerStatusEnum.ACCEPTED)
        return Mapper.entity_to_dto(response, GamePlayerResponseDTO)

    async def reject_join(self, game_id: UUID, player_id: UUID, requester_id: UUID) -> GamePlayerResponseDTO:
        game = await self.repo.get_by_id(game_id)
        if not game:
            raise GameNotFoundException()
        if game.author_id != requester_id:
            raise NotGameAuthorException()
        if not await self.repo.get_player(game_id, player_id):
            raise PlayerNotFoundException()
        response = await self.repo.update_player_status(game_id, player_id, PlayerStatusEnum.REJECTED)
        return Mapper.entity_to_dto(response, GamePlayerResponseDTO)

    async def remove_player(self, game_id: UUID, player_id: UUID, requester_id: UUID) -> None:
        game = await self.repo.get_by_id(game_id)
        if not game:
            raise GameNotFoundException()

        is_author = game.author_id == requester_id
        is_self = player_id == requester_id

        if not is_author and not is_self:
            raise NotGameAuthorException()

        if not await self.repo.get_player(game_id, player_id):
            raise PlayerNotFoundException()

        await self.repo.remove_player(game_id, player_id)

    async def attach_character(self, game_id: UUID, character_id: UUID, requester_id: UUID) \
            -> CharacterResponseDTO:
        game = await self.repo.get_by_id(game_id)
        if not game:
            raise GameNotFoundException()

        character = await self.character_repo.get_by_id(character_id)
        if not character:
            raise CharacterNotFoundException()

        # Только автор игры или владелец персонажа
        is_author = game.author_id == requester_id
        is_owner = character.user_id == requester_id
        if not is_author and not is_owner:
            raise CharacterPermissionException()

        # Игрок может добавить только одного персонажа
        if not is_author:
            existing = await self.character_repo.get_by_game_id_and_user_ids(
                game_id=game_id,
                user_ids=[requester_id],
                offset=0,
                limit=1
            )
            if existing:
                raise CharacterAlreadyExistsException()

        # Проверка game_system
        if character.game_system_id is None:
            raise CharacterGameSystemMismatchException(
                "Character must have a game system to join a game"
            )
        if character.game_system_id != game.game_system_id:
            raise CharacterGameSystemMismatchException(
                "Character game system does not match the game"
            )

        # Уникальность имени в игре
        if await self.character_repo.get_by_name_and_game_id(character.name, game_id):
            raise CharacterAlreadyExistsException()

        response = await self.character_repo.attach_to_game(character_id, game_id)
        return Mapper.entity_to_dto(response, CharacterResponseDTO)

    async def detach_character(self, game_id: UUID, character_id: UUID, requester_id: UUID) -> None:
        game = await self.repo.get_by_id(game_id)
        if not game:
            raise GameNotFoundException()

        character = await self.character_repo.get_by_id(character_id)
        if not character:
            raise CharacterNotFoundException()

        is_author = game.author_id == requester_id
        is_owner = character.user_id == requester_id
        if not is_author and not is_owner:
            raise CharacterPermissionException()

        await self.character_repo.detach_from_game(character_id)




