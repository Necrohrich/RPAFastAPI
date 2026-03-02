#app/api/security.py
from fastapi import Depends
from app.api.dependencies import get_current_user
from app.domain.policies.platform_policies import PlatformPolicies
from app.dto.auth_dtos import UserDTO


def require_superadmin(
    current_user: UserDTO = Depends(get_current_user),
):
    PlatformPolicies.require_superadmin(current_user)
    return current_user


def require_moderator(
    current_user: UserDTO = Depends(get_current_user),
):
    PlatformPolicies.require_moderator(current_user)
    return current_user


def require_support(
    current_user: UserDTO = Depends(get_current_user),
):
    PlatformPolicies.require_support(current_user)
    return current_user