"""FastAPI dependencies: authentication and shared objects."""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status

from app.core.security import InvalidTokenError, verify_firebase_token
from app.models.user import CurrentUser
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.utils.exceptions import INVALID_TOKEN_DETAIL, TOKEN_MISSING_DETAIL


async def get_bearer_token(
    authorization: Annotated[Optional[str], Header()] = None,
) -> str:
    """Extract and validate the `Authorization: Bearer <token>` header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=TOKEN_MISSING_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token.strip()


def get_user_repository() -> UserRepository:
    """Provide a UserRepository dependency."""
    return UserRepository()


def get_user_service(
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    """Provide a UserService dependency."""
    return UserService(repo)


async def get_current_user(
    token: Annotated[str, Depends(get_bearer_token)],
) -> CurrentUser:
    """Dependency that verifies the Firebase ID token and returns the user.

    Raises HTTPException(401) if the token is invalid.
    """
    try:
        claims = verify_firebase_token(token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    uid = claims.get("uid")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(
        uid=uid,
        email=claims.get("email"),
        name=claims.get("name"),
        phone_number=claims.get("phone_number"),
        email_verified=claims.get("email_verified", False),
    )


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
