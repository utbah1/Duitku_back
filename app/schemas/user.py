"""User schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserProfileOut(BaseModel):
    """User profile response."""

    model_config = ConfigDict(from_attributes=True)

    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: Optional[str] = None


class UserUpdateRequest(BaseModel):
    """Payload for PUT /api/v1/users/me."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(None, max_length=120)
    photo_url: Optional[str] = None
