"""Firestore-backed user model and the authenticated user data object."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass(slots=True)
class UserProfile:
    """Represents a user document stored in Firestore `users/{uid}`."""

    uid: str
    email: str
    name: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "email": self.email,
            "name": self.name,
            "photo_url": self.photo_url,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, uid: str, data: dict[str, Any]) -> "UserProfile":
        created = data.get("created_at")
        if isinstance(created, datetime):
            created = created
        return cls(
            uid=uid,
            email=data.get("email", ""),
            name=data.get("name"),
            photo_url=data.get("photo_url"),
            created_at=created,
        )


@dataclass(slots=True)
class CurrentUser:
    """The authenticated user derived from a verified Firebase ID token."""

    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email_verified: bool = False
    # Mutable list for extra claims if needed later.
    __extra: list[Any] = field(default_factory=list, init=False, repr=False)

    @property
    def identity(self) -> str:
        return self.uid

