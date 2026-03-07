# app/validators/game_system_validators.py
from app.exceptions.common_exceptions import ValidationError


class GameSystemValidator:

    @staticmethod
    def validate_name(name: str) -> None:
        name = name.strip()
        if not name:
            raise ValidationError("Game system name cannot be empty")
        if len(name) > 255:
            raise ValidationError("Game system name must be 255 characters or less")

    @staticmethod
    def validate_description(description: str) -> None:
        if len(description) > 4000:
            raise ValidationError("Description must be 4000 characters or less")