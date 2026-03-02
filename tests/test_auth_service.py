import pytest
from uuid import uuid4
from unittest.mock import AsyncMock

from app.services.auth_service import AuthService
from app.domain.entities.user import User
from app.dto.auth_dtos import RegisterRequestDTO
from app.exceptions.auth_exceptions import InvalidCredentials


@pytest.fixture
def user_repo():
    return AsyncMock()


@pytest.fixture
def token_repo():
    return AsyncMock()


@pytest.fixture
def auth_service(user_repo, token_repo):
    return AuthService(user_repo=user_repo, token_repo=token_repo)


@pytest.mark.asyncio
async def test_register_success(auth_service, user_repo, token_repo):

    # Arrange
    dto = RegisterRequestDTO(
        login="testuser",
        email="test@example.com",
        password="StrongPass1!"
    )

    user_repo.create = AsyncMock()
    token_repo.create = AsyncMock()

    # Act
    response = await auth_service.register(dto)

    # Assert
    assert response.access_token is not None
    assert response.refresh_token is not None
    user_repo.create.assert_called_once()
    token_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_login_invalid_credentials(auth_service, user_repo):

    # Arrange
    user_repo.get_by_email = AsyncMock(return_value=None)

    from app.dto.auth_dtos import LoginRequestDTO

    dto = LoginRequestDTO(
        email="wrong@example.com",
        password="12345678"
    )

    # Act & Assert
    with pytest.raises(InvalidCredentials):
        await auth_service.login(dto)