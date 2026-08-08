"""User business logic."""
from __future__ import annotations

from typing import Any, Optional

from app.models.user import UserProfile
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import NotFoundError, USER_NOT_FOUND_DETAIL


class UserService:
    """Handles operations on the authenticated user's profile."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def get_me(self, uid: str) -> UserProfile:
        profile = self.repo.get_by_id(uid)
        if profile is None:
            # Auto-create a profile from the verified token if missing.
            raise NotFoundError(USER_NOT_FOUND_DETAIL)
        return profile

    def get_or_create(self, uid: str, email: str, name: Optional[str] = None) -> UserProfile:
        return self.repo.upsert(uid, email=email, name=name)

    def update_me(self, uid: str, name: Optional[str], photo_url: Optional[str]) -> UserProfile:
        """Update the user's own profile fields."""
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if photo_url is not None:
            data["photo_url"] = photo_url
        if not data:
            return self.get_me(uid)
        updated = self.repo.update(uid, data)
        if updated is None:
            raise NotFoundError(USER_NOT_FOUND_DETAIL)
        return updated

    def delete_me(self, uid: str) -> None:
        """Delete the user's profile (and optionally more later)."""
        deleted = self.repo.delete(uid)
        if not deleted:
            raise NotFoundError(USER_NOT_FOUND_DETAIL)
