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
    "GameSystemHasDependenciesException",
    "CharacterError",
    "CharacterNotFoundException",
    "CharacterAlreadyExistsException",
    "CharacterGameSystemMismatchException",
    "CharacterPermissionException",
    "GameError",
    "GameNotFoundException",
    "GameAlreadyExistsException",
    "PlayerAlreadyInGameException",
    "PlayerNotFoundException",
    "NotGameAuthorException",
]


from app.exceptions.auth_exceptions import TokenExpired, AuthError, InvalidToken, InvalidCredentials
from app.exceptions.character_exceptions import CharacterPermissionException, CharacterGameSystemMismatchException, \
    CharacterAlreadyExistsException, CharacterNotFoundException, CharacterError
from app.exceptions.common_exceptions import PermissionDenied, NotFoundError, ApplicationError, ValidationError
from app.exceptions.game_exceptions import NotGameAuthorException, PlayerNotFoundException, \
    PlayerAlreadyInGameException, GameAlreadyExistsException, GameNotFoundException, GameError
from app.exceptions.game_system_exceptions import GameSystemAlreadyExistsException, GameSystemNotFoundException, \
    GameSystemError, GameSystemHasDependenciesException
from app.exceptions.user_exceptions import PasswordWrongError, PasswordSameError, DiscordSameAsPrimary, \
    DiscordAlreadyLinked, EmailSameAsPrimary, EmailAlreadyExists, LoginAlreadyExists, UserError
