# app/infrastructure/repositories/exception_handlers.py
from sqlalchemy.exc import IntegrityError

from app.exceptions import CharacterAlreadyExistsException, GameAlreadyExistsException, PlayerAlreadyInGameException
from app.exceptions.user_exceptions import LoginAlreadyExists, EmailAlreadyExists, DiscordAlreadyLinked

def handle_user_integrity_error(e: IntegrityError) -> None:
    error_str = str(e.orig)

    if "ix_users_primary_email" in error_str:
        raise EmailAlreadyExists("Этот primary email уже занят")
    if "ix_users_secondary_email" in error_str or "users_secondary_email" in error_str:
        raise EmailAlreadyExists("Этот secondary email уже занят")
    if "uq_users_email_global" in error_str:
        raise EmailAlreadyExists("Такая комбинация email уже существует")
    if "ix_users_login" in error_str:
        raise LoginAlreadyExists("Этот логин уже занят")
    if "ix_users_primary_discord_id" in error_str:
        raise DiscordAlreadyLinked("Этот Discord аккаунт уже привязан как основной")
    if "ix_users_secondary_discord_id" in error_str:
        raise DiscordAlreadyLinked("Этот Discord аккаунт уже привязан как дополнительный")
    if "uq_users_discord_id_global" in error_str:
        raise DiscordAlreadyLinked("Такая комбинация Discord ID уже существует")
    # Character
    if "uq_character_name_game" in error_str:
        raise CharacterAlreadyExistsException("Персонаж с таким именем уже существует в этой игре")

    # Game
    if "uq_game_name_author" in error_str:
        raise GameAlreadyExistsException("Игра с таким названием уже существует")

    # Game players
    if "game_players" in error_str:
        raise PlayerAlreadyInGameException("Игрок уже является участником этой игры")

    raise e