#app/services/user_service.py
from uuid import UUID

from app.domain.enums.platform_role_enum import PlatformRoleEnum
from app.domain.repositories.auth_repositories.discord_repositories import IDiscordRepository
from app.domain.repositories.auth_repositories.user_repository import IUserRepository
from app.dto.auth_dtos import UserDTO
from app.exceptions.common_exceptions import NotFoundError
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

        Responsibilities:
            - Uses UserRepository and DiscordRepository
            - Applies business rules related to user profile
            - Invalidates sessions when required (e.g., password change)

        Does NOT:
            - Handle authentication flow
            - Generate tokens
            - Contain infrastructure logic
        """

    def __init__(self, user_repo: IUserRepository, discord_repo: IDiscordRepository):
        self.user_repo = user_repo
        self.discord_repo = discord_repo

    async def change_password(self, user_id: UUID, new_password: str):

        PasswordValidator.validate_strength(new_password)

        password_hash = PasswordHasher.hash(new_password)

        await self.user_repo.update_password(user_id, password_hash)

        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise NotFoundError()

        await self.user_repo.update_token_version(
            user_id,
            user.token_version + 1
        )

    async def update_role(self, user_id: UUID, role: PlatformRoleEnum):
        RoleValidator.validate_role(role)
        await self.user_repo.update_role(user_id, role)

    async def attach_secondary_email(self, user_id: UUID, email: str):

        await self.user_repo.attach_secondary_email(user_id, email)

    async def attach_primary_discord_id(self, user_id: UUID, discord_id: int):
        DiscordValidator.validate_discord_id(discord_id)
        await self.discord_repo.attach_priority(user_id, discord_id)

    async def attach_secondary_discord_id(self, user_id: UUID, discord_id: int):
        DiscordValidator.validate_discord_id(discord_id)
        await self.discord_repo.attach_secondary(user_id, discord_id)

    async def get_user_by_discord(self, discord_id: int) -> UserDTO:
        user = await self.discord_repo.get_user_by_discord_id(discord_id)

        if not user:
            raise NotFoundError()

        return Mapper.entity_to_dto(user, UserDTO)