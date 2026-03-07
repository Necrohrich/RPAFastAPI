# app/validators/game_validators.py
from app.exceptions.common_exceptions import ValidationError
from app.validators.user_validators import DiscordValidator

class GameValidator:

    @staticmethod
    def validate_name(name: str) -> None:
        name = name.strip()
        if not name:
            raise ValidationError("Game name cannot be empty")
        if len(name) > 255:
            raise ValidationError("Game name must be 255 characters or less")

    @staticmethod
    def validate_discord_ids(
            discord_role_id: int | None,
            discord_channel_id: int | None
    ) -> None:
        """Валидирует Discord поля если они переданы"""
        if discord_role_id is not None:
            DiscordValidator.validate_discord_id(discord_role_id)
        if discord_channel_id is not None:
            DiscordValidator.validate_discord_id(discord_channel_id)