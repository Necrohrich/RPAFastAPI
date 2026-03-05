#app/api/exception_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import status
from sqlalchemy.exc import IntegrityError

from app.exceptions.auth_exceptions import (
    InvalidCredentials,
    InvalidToken,
    TokenExpired
)
from app.exceptions.common_exceptions import NotFoundError, ValidationError, PermissionDenied
from app.exceptions.user_exceptions import (
    LoginAlreadyExists,
    EmailAlreadyExists,
    DiscordAlreadyLinked,
    PasswordSameError,
    PasswordWrongError,
)

async def invalid_credentials_handler(request: Request, exc: InvalidCredentials):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid credentials"}
    )


async def invalid_token_handler(request: Request, exc: InvalidToken):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid token"}
    )


async def token_expired_handler(request: Request, exc: TokenExpired):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Token expired"}
    )


async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Not found"}
    )

async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )

async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Database constraint error"}
    )

async def permission_denied_handler(request: Request, exc: PermissionDenied):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc) or "Forbidden"}
    )

async def login_already_exists_handler(request: Request, exc: LoginAlreadyExists):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Login already exists"}
    )

async def email_already_exists_handler(request: Request, exc: EmailAlreadyExists):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Email already exists"}
    )

async def discord_already_linked_handler(request: Request, exc: DiscordAlreadyLinked):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Discord already linked"}
    )

async def password_same_error_handler(request: Request, exc: PasswordSameError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "New password must differ from the current one"}
    )

async def password_wrong_error_handler(request: Request, exc: PasswordWrongError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Old password is incorrect"}
    )