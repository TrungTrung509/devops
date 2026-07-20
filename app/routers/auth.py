from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from schemas.Auth import Token
from services.AuthService import AuthService, get_auth_service

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.login(form_data.username, form_data.password)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.refresh(payload.refresh_token)


@router.post("/logout")
async def logout(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.logout(payload.refresh_token)
    return {"message": "Dang xuat thanh cong"}
