"""Authentication schemas (register, login, logout, me)."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Payload for POST /api/v1/auth/register.

    The user's password is handled by Firebase Authentication via the REST
    API; the backend never stores it.
    """

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(..., description="User email address.")
    password: str = Field(..., min_length=6, max_length=128)
    name: Optional[str] = Field(None, max_length=120)


class LoginRequest(BaseModel):
    """Payload for POST /api/v1/auth/login.

    Exchanges email/password for a Firebase ID token (via Firebase REST API)
    and returns a signed DuitKu access token along with the user details.
    """

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(..., min_length=1)


class UpdateProfileRequest(BaseModel):
    """Payload for updating the user's profile (used in auth/me as well)."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(None, max_length=120)
    photo_url: Optional[str] = None


class UserOut(BaseModel):
    """Public user response object."""

    model_config = ConfigDict(from_attributes=True)

    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: Optional[str] = None


class TokenResponse(BaseModel):
    """Response returned after login / register."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LogoutResponse(BaseModel):
    """Response returned after logout."""

    message: str = "Logged out successfully"
