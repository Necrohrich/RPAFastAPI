# app/domain/policies/platform_policies.py

from app.domain.enums.platform_role_enum import PlatformRoleEnum
from app.domain.entities.user import User
from .base_policy import BasePolicy


class PlatformPolicies(BasePolicy):


    @staticmethod
    def require_superadmin(user: User) -> None:
        if user.platform_role != PlatformRoleEnum.SUPERADMIN:
            BasePolicy.deny("Superadmin only")

    @staticmethod
    def require_moderator(user: User) -> None:
        if user.platform_role not in (
            PlatformRoleEnum.SUPERADMIN,
            PlatformRoleEnum.MODERATOR,
        ):
            BasePolicy.deny("Moderator or higher required")

    @staticmethod
    def require_support(user: User) -> None:
        if user.platform_role not in (
            PlatformRoleEnum.SUPERADMIN,
            PlatformRoleEnum.MODERATOR,
            PlatformRoleEnum.SUPPORT,
        ):
            BasePolicy.deny("Support or higher required")