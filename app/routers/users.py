"""User profile endpoints (scoped to the authenticated user)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.dependencies import CurrentUserDep
from app.core.firebase import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserOut
from app.schemas.user import UserProfileOut, UserUpdateRequest
from app.services.user_service import UserService
from app.utils.response import success_response

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service() -> UserService:
    return UserService(UserRepository(get_db()))


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def _profile_out(profile) -> dict:
    return {
        "uid": profile.uid,
        "email": profile.email,
        "name": profile.name,
        "photo_url": getattr(profile, "photo_url", None),
        "created_at": (
            profile.created_at.isoformat() if getattr(profile, "created_at", None) else None
        ),
    }


@router.get("/me/profile", response_model=UserProfileOut)
async def get_profile(current_user: CurrentUserDep, service: UserServiceDep):
    profile = service.repo.upsert(
        current_user.uid,
        email=current_user.email or "",
        name=current_user.name,
    )
    return _profile_out(profile)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CurrentUserDep, service: UserServiceDep):
    profile = service.repo.upsert(
        current_user.uid,
        email=current_user.email or "",
        name=current_user.name,
    )
    return _profile_out(profile)


@router.put("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdateRequest,
    current_user: CurrentUserDep,
    service: UserServiceDep,
):
    # Ensure profile exists before updating
    service.repo.upsert(
        current_user.uid,
        email=current_user.email or "",
        name=current_user.name,
    )
    profile = service.update_me(
        current_user.uid, name=payload.name, photo_url=payload.photo_url
    )
    return _profile_out(profile)


@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_me(
    current_user: CurrentUserDep,
    service: UserServiceDep,
    response: Response,
):
    service.delete_me(current_user.uid)
    return success_response("User deleted successfully", None)
