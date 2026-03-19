# app/api/exception_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import status
from sqlalchemy.exc import IntegrityError

from app.exceptions import CharacterPermissionException, CharacterGameSystemMismatchException, \
    CharacterAlreadyExistsException, CharacterNotFoundException, NotGameAuthorException, PlayerNotFoundException, \
    PlayerAlreadyInGameException, GameAlreadyExistsException, GameNotFoundException, GameSystemAlreadyExistsException, \
    GameSystemNotFoundException, GameSystemHasDependenciesException, CharacterGameSystemAlreadySetException, \
    GameSessionInvalidStatusTransitionException, GameSessionAlreadyActiveException, GameSessionNotFoundException, \
    GameReviewNotFoundException, GameReviewInvalidStatusTransitionException, GameReviewNotAllowedException, \
    GameReviewAlreadySentException, GameReviewAlreadyExistsException
from app.exceptions.auth_exceptions import InvalidCredentials, InvalidToken, TokenExpired
from app.exceptions.common_exceptions import NotFoundError, ValidationError, PermissionDenied
from app.exceptions.user_exceptions import (
    LoginAlreadyExists, EmailAlreadyExists, DiscordAlreadyLinked,
    PasswordSameError, PasswordWrongError, DiscordSameAsPrimary, EmailSameAsPrimary,
)

EXCEPTION_MAP: dict[type[Exception], tuple[int, str]] = {
    # Auth
    InvalidCredentials:                 (status.HTTP_401_UNAUTHORIZED,  "Invalid credentials"),
    InvalidToken:                       (status.HTTP_401_UNAUTHORIZED,  "Invalid token"),
    TokenExpired:                       (status.HTTP_401_UNAUTHORIZED,  "Token expired"),

    # Common
    NotFoundError:                      (status.HTTP_404_NOT_FOUND,     "Not found"),
    PermissionDenied:                   (status.HTTP_403_FORBIDDEN,     "Forbidden"),

    # User
    LoginAlreadyExists:                 (status.HTTP_409_CONFLICT,      "Login already exists"),
    EmailAlreadyExists:                 (status.HTTP_409_CONFLICT,      "Email already exists"),
    EmailSameAsPrimary:                 (status.HTTP_409_CONFLICT,      "Secondary email cannot be the same as primary"),
    DiscordAlreadyLinked:               (status.HTTP_409_CONFLICT,      "Discord already linked"),
    DiscordSameAsPrimary:               (status.HTTP_409_CONFLICT,      "Secondary Discord ID cannot be the same as primary"),
    PasswordSameError:                  (status.HTTP_400_BAD_REQUEST,   "New password must differ from the current one"),
    PasswordWrongError:                 (status.HTTP_400_BAD_REQUEST,   "Old password is incorrect"),

    # Game system
    GameSystemNotFoundException:        (status.HTTP_404_NOT_FOUND,     "Game system not found"),
    GameSystemAlreadyExistsException:   (status.HTTP_409_CONFLICT,      "Game system already exists"),
    GameSystemHasDependenciesException: (status.HTTP_409_CONFLICT,      "Game system has dependencies"),

    # Game
    GameNotFoundException:              (status.HTTP_404_NOT_FOUND,     "Game not found"),
    GameAlreadyExistsException:         (status.HTTP_409_CONFLICT,      "Game with this name already exists"),
    PlayerAlreadyInGameException:       (status.HTTP_409_CONFLICT,      "Player already in game or request is pending"),
    PlayerNotFoundException:            (status.HTTP_404_NOT_FOUND,     "Player not found in this game"),
    NotGameAuthorException:             (status.HTTP_403_FORBIDDEN,     "Only the game author can perform this action"),

    # Character
    CharacterNotFoundException:         (status.HTTP_404_NOT_FOUND,     "Character not found"),
    CharacterAlreadyExistsException:    (status.HTTP_409_CONFLICT,      "Character with this name already exists in the game"),
    CharacterGameSystemMismatchException: (status.HTTP_409_CONFLICT,    "Character game system does not match the game"),
    CharacterPermissionException:       (status.HTTP_403_FORBIDDEN,     "Only the character owner can perform this action"),
    CharacterGameSystemAlreadySetException: (status.HTTP_409_CONFLICT, "Character game system already set"),

    # Game Session
    GameSessionNotFoundException:                   (status.HTTP_404_NOT_FOUND,   "Game session not found"),
    GameSessionAlreadyActiveException:              (status.HTTP_409_CONFLICT,    "Game already has an active session"),
    GameSessionInvalidStatusTransitionException:    (status.HTTP_409_CONFLICT,    "Invalid session status transition"),

    # Game Review
    GameReviewNotFoundException:                    (status.HTTP_404_NOT_FOUND,   "Game review not found"),
    GameReviewAlreadyExistsException:               (status.HTTP_409_CONFLICT,    "Player already submitted a review for this session"),
    GameReviewAlreadySentException:                 (status.HTTP_409_CONFLICT,    "Review has already been sent and cannot be modified"),
    GameReviewNotAllowedException:                  (status.HTTP_403_FORBIDDEN,   "User is not allowed to leave a review for this session"),
    GameReviewInvalidStatusTransitionException:     (status.HTTP_409_CONFLICT,    "Invalid review status transition"),
}


async def app_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    status_code, detail = EXCEPTION_MAP.get(
        type(exc),
        (status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error")
    )
    return JSONResponse(status_code=status_code, content={"detail": detail})


async def validation_error_handler(_: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})


async def integrity_error_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Database constraint error"})