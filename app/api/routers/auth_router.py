# app/api/routers/auth_router.py

from fastapi import APIRouter, Depends, status
from app.dto.auth_dtos import (
    RegisterRequestDTO,
    AuthResponseDTO,
    LoginRequestDTO,
    RefreshRequestDTO, UserDTO,
)
from app.services.auth_service import AuthService
from app.api.dependencies import get_auth_service, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=AuthResponseDTO, status_code=status.HTTP_201_CREATED)
async def register(
        dto: RegisterRequestDTO,
        service: AuthService = Depends(get_auth_service),
):
    return await service.register(dto)


@router.post("/login", response_model=AuthResponseDTO)
async def login(
        dto: LoginRequestDTO,
        service: AuthService = Depends(get_auth_service),
):
    return await service.login(dto)


@router.post("/refresh", response_model=AuthResponseDTO)
async def refresh(
        dto: RefreshRequestDTO,
        service: AuthService = Depends(get_auth_service),
):
    return await service.refresh(dto)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
        dto: RefreshRequestDTO,
        service: AuthService = Depends(get_auth_service),
):
    await service.logout(dto.refresh_token)

@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
        current_user: UserDTO = Depends(get_current_user),
        service: AuthService = Depends(get_auth_service),
):
    await service.logout_all(current_user.id)