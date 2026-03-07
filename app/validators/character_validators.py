# app/validators/character_validators.py
from typing import Optional
from uuid import UUID

from app.exceptions.common_exceptions import ValidationError
from app.exceptions.character_exceptions import CharacterGameSystemMismatchException


class CharacterValidator:

    @staticmethod
    def validate_name(name: str) -> None:
        name = name.strip()
        if not name:
            raise ValidationError("Character name cannot be empty")
        if len(name) > 255:
            raise ValidationError("Character name must be 255 characters or less")

    @staticmethod
    def validate_game_system_match(
        character_game_system_id: Optional[UUID],
        game_game_system_id: UUID
    ) -> None:
        """Проверяет совместимость game_system персонажа и игры при привязке к игре"""
        if character_game_system_id is None:
            return
        if character_game_system_id != game_game_system_id:
            raise CharacterGameSystemMismatchException(
                "Character game system does not match the game system of the selected game"
            )