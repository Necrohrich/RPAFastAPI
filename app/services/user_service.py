#app/services/user_service.py
from uuid import UUID

from app.domain.enums.platform_role_enum import PlatformRoleEnum
from app.domain.repositories.auth_repositories.discord_repositories import IDiscordRepository
from app.domain.repositories.auth_repositories.user_repository import IUserRepository
from app.dto import PaginatedResponseDTO, GameResponseDTO, CharacterResponseDTO
from app.dto.auth_dtos import UserDTO, ChangePasswordDTO
from app.exceptions.common_exceptions import NotFoundError
from app.exceptions.user_exceptions import PasswordSameError, PasswordWrongError, DiscordAlreadyLinked, \
    DiscordSameAsPrimary, EmailSameAsPrimary, EmailAlreadyExists
from app.infrastructure.security.password_hasher import PasswordHasher
from app.utils.mapper import Mapper
from app.validators.auth_validators import PasswordValidator
from app.validators.user_validators import DiscordValidator, RoleValidator


class UserService:
    """
       Application service responsible for user profile management.

       Handles:
           - Password changes
           - Role updates
           - Email management
           - Discord account linking
           - User retrieval by Discord ID
           - Paginated retrieval of user's authored games, participated games and characters

       Responsibilities:
           - Uses IUserRepository and IDiscordRepository
           - Applies business rules related to user profile
           - Invalidates sessions when required (e.g., password change)

       Does NOT:
           - Handle authentication flow
           - Generate tokens
           - Manage game or character CRUD directly
           - Contain infrastructure logic
    """

    def __init__(self, user_repo: IUserRepository, discord_repo: IDiscordRepository):
        self.user_repo = user_repo
        self.discord_repo = discord_repo

    async def change_password(self, user_id: UUID, dto: ChangePasswordDTO):

        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise NotFoundError()

        if not PasswordHasher.verify(dto.old_password, user.password_hash):
            raise PasswordWrongError()

        PasswordValidator.validate_strength(dto.new_password)

        if dto.old_password == dto.new_password:
            raise PasswordSameError()

        new_password_hash = PasswordHasher.hash(dto.new_password)

        await self.user_repo.update_password(user.id, new_password_hash)

        await self.user_repo.update_token_version(
            user.id,
            user.token_version + 1
        )

    async def update_role(self, user_id: UUID, role: PlatformRoleEnum):
        if role is not None:
            RoleValidator.validate_role(role)

        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise NotFoundError()

        await self.user_repo.update_role(user_id, role)

    async def attach_secondary_email(self, user_id: UUID, email: str):

        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise NotFoundError()

        if user.primary_email == email:
            raise EmailSameAsPrimary()

        check_user = await self.user_repo.get_by_email(email)

        if check_user:
            raise EmailAlreadyExists()

        await self.user_repo.attach_secondary_email(user_id, email)

    async def attach_primary_discord_id(self, user_id: UUID, discord_id: int):
        DiscordValidator.validate_discord_id(discord_id)

        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise NotFoundError()

        check_user = await self.discord_repo.get_user_by_discord_id(discord_id)

        if check_user:
            raise DiscordAlreadyLinked()

        await self.discord_repo.attach_priority(user_id, discord_id)

    async def attach_secondary_discord_id(self, user_id: UUID, discord_id: int):
        DiscordValidator.validate_discord_id(discord_id)

        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise NotFoundError()

        if user.primary_discord_id == discord_id:
            raise DiscordSameAsPrimary()

        check_user = await self.discord_repo.get_user_by_discord_id(discord_id)

        if check_user:
            raise DiscordAlreadyLinked()

        await self.discord_repo.attach_secondary(user_id, discord_id)

    async def get_user_by_discord(self, discord_id: int) -> UserDTO:
        user = await self.discord_repo.get_user_by_discord_id(discord_id)

        if not user:
            raise NotFoundError()

        return Mapper.entity_to_dto(user, UserDTO)

    async def get_my_games(self, user_id: UUID, page: int, page_size: int) \
            -> PaginatedResponseDTO[GameResponseDTO]:
        if not await self.user_repo.get_by_id(user_id):
            raise NotFoundError()
        offset = (page - 1) * page_size
        items = await self.user_repo.get_my_games(user_id, offset=offset, limit=page_size)
        total = await self.user_repo.count_my_games(user_id)
        return PaginatedResponseDTO(
            items=[Mapper.entity_to_dto(item, GameResponseDTO) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    async def get_participated_games(self, user_id: UUID, page: int, page_size: int) \
            -> PaginatedResponseDTO[GameResponseDTO]:
        if not await self.user_repo.get_by_id(user_id):
            raise NotFoundError()
        offset = (page - 1) * page_size
        items = await self.user_repo.get_participated_games(user_id, offset=offset, limit=page_size)
        total = await self.user_repo.count_participated_games(user_id)
        return PaginatedResponseDTO(
            items=[Mapper.entity_to_dto(item, GameResponseDTO) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    async def get_my_characters(self, user_id: UUID, page: int, page_size: int) \
            -> PaginatedResponseDTO[CharacterResponseDTO]:
        if not await self.user_repo.get_by_id(user_id):
            raise NotFoundError()
        offset = (page - 1) * page_size
        items = await self.user_repo.get_my_characters(user_id, offset=offset, limit=page_size)
        total = await self.user_repo.count_my_characters(user_id)
        return PaginatedResponseDTO(
            items=[Mapper.entity_to_dto(item, CharacterResponseDTO) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )