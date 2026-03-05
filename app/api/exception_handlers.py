# app/api/exception_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import status
from sqlalchemy.exc import IntegrityError

from app.exceptions.auth_exceptions import InvalidCredentials, InvalidToken, TokenExpired
from app.exceptions.common_exceptions import NotFoundError, ValidationError, PermissionDenied
from app.exceptions.user_exceptions import (
    LoginAlreadyExists, EmailAlreadyExists, DiscordAlreadyLinked,
    PasswordSameError, PasswordWrongError, DiscordSameAsPrimary, EmailSameAsPrimary,
)

EXCEPTION_MAP: dict[type[Exception], tuple[int, str]] = {
    InvalidCredentials:   (status.HTTP_401_UNAUTHORIZED, "Invalid credentials"),
    InvalidToken:         (status.HTTP_401_UNAUTHORIZED, "Invalid token"),
    TokenExpired:         (status.HTTP_401_UNAUTHORIZED, "Token expired"),
    NotFoundError:        (status.HTTP_404_NOT_FOUND, "Not found"),
    PermissionDenied:     (status.HTTP_403_FORBIDDEN, "Forbidden"),
    LoginAlreadyExists:   (status.HTTP_409_CONFLICT, "Login already exists"),
    EmailAlreadyExists:   (status.HTTP_409_CONFLICT, "Email already exists"),
    EmailSameAsPrimary:   (status.HTTP_409_CONFLICT, "Secondary Email cannot be the same as primary"),
    DiscordAlreadyLinked: (status.HTTP_409_CONFLICT, "Discord already linked"),
    DiscordSameAsPrimary: (status.HTTP_409_CONFLICT, "Secondary Discord ID cannot be the same as primary"),
    PasswordSameError:    (status.HTTP_400_BAD_REQUEST, "New password must differ from the current one"),
    PasswordWrongError:   (status.HTTP_400_BAD_REQUEST, "Old password is incorrect"),
}

async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code, detail = EXCEPTION_MAP.get(type(exc), (status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error"))
    return JSONResponse(status_code=status_code, content={"detail": detail})


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Database constraint error"})