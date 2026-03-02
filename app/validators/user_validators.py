#app/validators/user_validators.py
from app.domain.enums.platform_role_enum import PlatformRoleEnum
from app.exceptions.common_exceptions import ValidationError


class DiscordValidator:

    @staticmethod
    def validate_discord_id(discord_id: int) -> None:
        # Discord snowflake must be positive
        if not isinstance(discord_id, int):
            raise ValidationError("Discord ID must be integer")

        if discord_id <= 0:
            raise ValidationError("Invalid Discord ID")

        # Snowflake минимальный размер (примерная защита)
        if discord_id < 10_000_000_000_000_000:
            raise ValidationError("Invalid Discord Snowflake format")


class RoleValidator:

    @staticmethod
    def validate_role(role: str | PlatformRoleEnum) -> None:

        if isinstance(role, str):
            try:
                role = PlatformRoleEnum(role)
            except ValueError:
                raise ValidationError("Invalid role value")

        if role not in PlatformRoleEnum:
            raise ValidationError("Role not allowed")