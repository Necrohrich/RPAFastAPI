# app/api/routers/admin_router.py

from fastapi import APIRouter, Depends, status
from uuid import UUID

from app.api.security import require_superadmin, require_support
from app.domain.enums.platform_role_enum import PlatformRoleEnum
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.api.dependencies import get_user_service, get_auth_service
from app.dto.auth_dtos import UserDTO

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_superadmin)]
)
async def logout_all(
        user_id: UUID,
        service: AuthService = Depends(get_auth_service),
):
    await service.logout_all(user_id)


@router.put(
    "/{user_id}/role",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_superadmin)]
)
async def update_role(
        user_id: UUID,
        role: PlatformRoleEnum,
        service: UserService = Depends(get_user_service),
):
    await service.update_role(user_id, role)


@router.get(
    "/discord/{discord_id}",
    response_model=UserDTO,
    dependencies=[Depends(require_support)]
)
async def get_user_by_discord(
        discord_id: int,
        service: UserService = Depends(get_user_service),
):
    return await service.get_user_by_discord(discord_id)