# app/api/routers/user_router.py

from fastapi import APIRouter, Depends, status
from app.services.user_service import UserService
from app.api.dependencies import get_user_service, get_current_user
from app.dto.auth_dtos import UserDTO, ChangePasswordDTO

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.get(
    "/me",
    response_model=UserDTO,
    dependencies=[Depends(get_current_user)]
)
async def get_me(
    current_user: UserDTO = Depends(get_current_user),
):
    return current_user


@router.put(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_user)]
)
async def change_my_password(
        dto: ChangePasswordDTO,
        current_user: UserDTO = Depends(get_current_user),
        service: UserService = Depends(get_user_service),
):
    await service.change_password(current_user.id, dto.new_password)