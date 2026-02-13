#app/domain/enums/platform_role_enum.py

from enum import Enum

class PlatformRoleEnum(str, Enum):
    """
        System role.

        Attributes:
            SUPERADMIN: All permissions.
            MODERATOR: Safety permissions.
            SUPPORT: Customer support permissions.
        """
    SUPERADMIN = "superadmin"
    MODERATOR = "moderator"
    SUPPORT = "support"
