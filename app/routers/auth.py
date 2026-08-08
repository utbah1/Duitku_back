"""Authentication endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUserDep
from app.core.firebase import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service() -> AuthService:
    return AuthService(UserRepository(get_db()))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def _user_out(profile) -> dict:
    return {
        "uid": profile.uid,
        "email": profile.email,
        "name": profile.name,
        "photo_url": getattr(profile, "photo_url", None),
        "created_at": (
            profile.created_at.isoformat() if getattr(profile, "created_at", None) else None
        ),
    }


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(payload: RegisterRequest, service: AuthServiceDep):
    token, profile = await service.register(
        email=payload.email, password=payload.password, name=payload.name
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_out(profile),
    }


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and obtain an access token",
)
async def login(payload: LoginRequest, service: AuthServiceDep):
    token, profile = await service.login(
        email=payload.email, password=payload.password
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_out(profile),
    }


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Log out (client discards the token)",
)
async def logout(current_user: CurrentUserDep):
    # With stateless JWT, the client simply discards the token on its side.
    return {"message": "Logged out successfully"}


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get the currently authenticated user",
)
async def me(
    current_user: CurrentUserDep,
    service: AuthServiceDep,
):
    profile = service.user_repo.get_by_id(current_user.uid)
    if profile is None:
        profile = service.user_repo.upsert(
            current_user.uid, email=current_user.email or "", name=current_user.name
        )
    return _user_out(profile)
