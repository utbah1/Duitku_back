"""Security helpers: Firebase ID token verification and JWT helpers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import settings


class InvalidTokenError(Exception):
    """Raised when a bearer token is invalid, expired, or malformed."""


class FirebaseTokenVerifier:
    """Verifies Firebase ID tokens using the Firebase Admin SDK.

    The verification is performed lazily against firebase_admin.auth. If
    Firebase is not configured (e.g. in tests), subclass this and override
    `verify_token` with a fake implementation.
    """

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify a Firebase ID token and return its decoded claims."""
        from firebase_admin import auth as firebase_auth

        try:
            decoded: dict[str, Any] = firebase_auth.verify_id_token(token)
        except Exception as exc:  # firebase_admin.auth.InvalidIdTokenError etc.
            raise InvalidTokenError("Invalid or expired Firebase ID token.") from exc
        if not decoded.get("uid"):
            raise InvalidTokenError("Token does not contain a valid uid.")
        return decoded


# A module-level verifier instance (overridable in tests).
token_verifier = FirebaseTokenVerifier()


def verify_firebase_token(token: str) -> dict[str, Any]:
    """Verify a Firebase ID token and return decoded claims."""
    return token_verifier.verify_token(token)


# ---------------------------------------------------------------------------
# Internal JWT helpers (used for issuing our own session tokens after login).
# ---------------------------------------------------------------------------
def create_access_token(
    subject: str,
    extra: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra:
        to_encode.update(extra)
    return jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an internal JWT access token."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except (JWTError, ValidationError) as exc:
        raise InvalidTokenError("Invalid or expired access token.") from exc
    return payload
