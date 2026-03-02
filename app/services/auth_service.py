#app/services/auth_service.py
from datetime import datetime, timezone, timedelta
from typing import Tuple
from uuid import uuid4, UUID

from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings
from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.user import User
from app.domain.repositories.auth_repositories.token_repository import ITokenRepository
from app.domain.repositories.auth_repositories.user_repository import IUserRepository
from app.dto.auth_dtos import RegisterRequestDTO, AuthResponseDTO, LoginRequestDTO, RefreshRequestDTO, UserDTO
from app.exceptions.auth_exceptions import InvalidCredentials, InvalidToken, TokenExpired
from app.infrastructure.security.jwt_provider import JWTProvider
from app.infrastructure.security.password_hasher import PasswordHasher
from app.infrastructure.security.refresh_token_provider import RefreshTokenProvider
from app.utils.mapper import Mapper
from app.validators.auth_validators import PasswordValidator, LoginValidator


class AuthService:
    """
        Application service responsible for authentication and session management.

        Handles:
            - User registration
            - User login (password-based)
            - JWT access token validation
            - Refresh token rotation
            - Logout (single session)
            - Logout from all devices
            - Current user retrieval

        Responsibilities:
            - Coordinates UserRepository and TokenRepository
            - Uses infrastructure security components (JWT, password hashing, refresh tokens)
            - Returns and accepts DTO objects at system boundaries
            - Does NOT handle HTTP or transport logic

        Security features:
            - Refresh tokens are stored as hashes
            - Access tokens contain token_version for global invalidation
            - Token rotation is supported
        """

    def __init__(
            self,
            user_repo: IUserRepository,
            token_repo: ITokenRepository
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def _create_tokens_for_user(self, user: User, device_info: str = "") -> Tuple[str, str]:

        access = JWTProvider.create_access_token(user_id=user.id, token_version=user.token_version)
        raw_refresh = RefreshTokenProvider.generate()
        hashed = RefreshTokenProvider.hash(raw_refresh)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_entity = RefreshToken(
            id=uuid4(),
            user_id=user.id,
            token_hash=hashed,
            expires_at=expires_at,
            revoked_at=None,
            device_info=device_info,
            replaced_by_token_id=None,
        )

        await self.token_repo.create(refresh_entity)

        return access, raw_refresh

    async def register(self, dto: RegisterRequestDTO) -> AuthResponseDTO:

        LoginValidator.validate(dto.login)
        PasswordValidator.validate_strength(dto.password)

        user = User(
            id=uuid4(),
            login=dto.login,
            primary_email=dto.email,
            secondary_email=None,
            password_hash=PasswordHasher.hash(dto.password),
            primary_discord_id=None,
            secondary_discord_id=None,
            platform_role=None,
            token_version=0,
        )

        await self.user_repo.create(user)

        access, refresh = await self._create_tokens_for_user(user)

        return AuthResponseDTO(
            access_token=access,
            refresh_token=refresh
        )

    async def login(self, dto: LoginRequestDTO) -> AuthResponseDTO:

        user = await self.user_repo.get_by_email(dto.email)

        if not user or not PasswordHasher.verify(dto.password, user.password_hash):
            raise InvalidCredentials()

        access, refresh = await self._create_tokens_for_user(
            user,
            device_info=dto.device_info or ""
        )

        return AuthResponseDTO(
            access_token=access,
            refresh_token=refresh
        )

    async def refresh(self, dto: RefreshRequestDTO) -> AuthResponseDTO:

        hashed = RefreshTokenProvider.hash(dto.refresh_token)

        token_entity = await self.token_repo.get(hashed)

        if token_entity is None:
            raise InvalidToken()

        if token_entity.revoked_at is not None:
            raise InvalidToken()

        now = datetime.now(timezone.utc)
        if token_entity.expires_at <= now:
            raise TokenExpired()

        user = await self.user_repo.get_by_id(token_entity.user_id)
        if user is None:
            raise InvalidToken()

        await self.token_repo.revoke(hashed)

        access, new_refresh = await self._create_tokens_for_user(
            user,
            device_info=dto.device_info
        )

        return AuthResponseDTO(
            access_token=access,
            refresh_token=new_refresh
        )

    async def get_current_user(self, access_token: str) -> UserDTO:

        try:
            payload = JWTProvider.decode_token(access_token)
        except ExpiredSignatureError:
            raise TokenExpired()
        except InvalidTokenError:
            raise InvalidToken()

        user_id = UUID(payload["sub"])
        token_version = payload.get("ver", 0)

        user = await self.user_repo.get_by_id(user_id)

        if user is None:
            raise InvalidToken()

        # Проверка version (очень важно)
        if user.token_version != token_version:
            raise InvalidToken()

        return Mapper.entity_to_dto(user, UserDTO)

    async def logout(self, raw_refresh_token: str) -> None:
        hashed = RefreshTokenProvider.hash(raw_refresh_token)
        await self.token_repo.revoke(hashed)

    async def logout_all(self, user_id: UUID) -> None:
        await self.token_repo.revoke_all(user_id)
        user = await self.user_repo.get_by_id(user_id)

        if user is None:
            raise InvalidToken()

        await self.user_repo.update_token_version(
            user_id,
            user.token_version + 1
        )