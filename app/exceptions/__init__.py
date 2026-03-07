# app/exceptions/__init__.py
__all__ = [
    "AuthError",
    "InvalidCredentials",
    "InvalidToken",
    "TokenExpired",
    "ApplicationError",
    "NotFoundError",
    "ValidationError",
    "PermissionDenied",
    "UserError",
    "LoginAlreadyExists",
    "EmailAlreadyExists",
    "EmailSameAsPrimary",
    "DiscordAlreadyLinked",
    "DiscordSameAsPrimary",
    "PasswordSameError",
    "PasswordWrongError",
    "GameSystemError",
    "GameSystemNotFoundException",
    "GameSystemAlreadyExistsException",
    "CharacterError",
    "CharacterNotFoundException",
    "CharacterAlreadyExistsException",
    "CharacterGameSystemMismatchException",
    "GameError",
    "GameNotFoundException",
    "GameAlreadyExistsException",
    "PlayerAlreadyInGameException",
    "PlayerNotFoundException",
    "NotGameAuthorException",
]

from app.exceptions.auth_exceptions import *
from app.exceptions.character_exceptions import *
from app.exceptions.common_exceptions import *
from app.exceptions.game_exceptions import *
from app.exceptions.game_system_exceptions import *
from app.exceptions.user_exceptions import *