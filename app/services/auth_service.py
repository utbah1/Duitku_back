"""Authentication business logic.

Firebase Authentication is the source of truth. The backend never stores
passwords. Register/login talk to the Firebase Auth REST API (using the
Firebase Web API key) to sign users up and exchange credentials for an ID
token; the backend then verifies that token and issues its own access token.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.models.user import UserProfile
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import (
    AUTH_SERVICE_UNAVAILABLE_DETAIL,
    ConflictError,
    UnauthorizedError,
)

logger = logging.getLogger(__name__)

FIREBASE_AUTH_BASE = "https://identitytoolkit.googleapis.com/v1"


class AuthService:
    """Handles Firebase Authentication REST interactions and user bootstrap."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def _api_key(self) -> str:
        if not settings.FIREBASE_API_KEY:
            raise UnauthorizedError(
                "Firebase API key is not configured. Set FIREBASE_API_KEY."
            )
        return settings.FIREBASE_API_KEY

    async def register(
        self, email: str, password: str, name: Optional[str] = None
    ) -> tuple[str, UserProfile]:
        """Create a Firebase Auth user, persist their profile, return an
        access token and the user profile."""
        id_token = await self._signup(email, password)
        uid = await self._resolve_uid(id_token)
        try:
            profile = self.user_repo.upsert(uid, email=email, name=name)
        except Exception:  # noqa: BLE001 - isolation of persistence errors
            logger.exception("Failed to persist user profile after signup.")
            raise
        access_token = self._issue_access_token(uid, email, name)
        return access_token, profile

    async def login(self, email: str, password: str) -> tuple[str, UserProfile]:
        """Sign in with Firebase, return an access token and the user profile."""
        id_token = await self._signin(email, password)
        uid = await self._resolve_uid(id_token)
        profile = self.user_repo.upsert(uid, email=email)
        access_token = self._issue_access_token(uid, email, profile.name)
        return access_token, profile

    async def _signup(self, email: str, password: str) -> str:
        url = f"{FIREBASE_AUTH_BASE}/accounts:signUp"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        }
        data = await self._post(url, payload)
        return data["idToken"]

    async def _signin(self, email: str, password: str) -> str:
        url = f"{FIREBASE_AUTH_BASE}/accounts:signInWithPassword"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        }
        data = await self._post(url, payload)
        return data["idToken"]

    async def _resolve_uid(self, id_token: str) -> str:
        """Verify the ID token via the Admin SDK to obtain the uid."""
        from firebase_admin import auth as firebase_auth

        try:
            decoded = firebase_auth.verify_id_token(id_token)
            return decoded["uid"]
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to verify token during auth flow.")
            raise UnauthorizedError("Unable to verify authentication token.") from exc

    async def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST to the Firebase Auth REST API and normalize errors."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    url, params={"key": self._api_key()}, json=payload
                )
        except httpx.HTTPError as exc:
            logger.exception("Firebase Auth REST call failed.")
            raise UnauthorizedError(AUTH_SERVICE_UNAVAILABLE_DETAIL) from exc

        if resp.status_code == 200:
            return resp.json()

        error_info = self._extract_firebase_error(resp.json())
        code = error_info["code"]
        message = error_info["message"]

        if code in ("EMAIL_EXISTS",):
            raise ConflictError("An account with this email already exists.")
        if code in ("EMAIL_NOT_FOUND", "INVALID_PASSWORD", "INVALID_LOGIN_CREDENTIALS"):
            raise UnauthorizedError("Invalid email or password.")

        raise UnauthorizedError(message or "Authentication failed.")

    def _issue_access_token(self, uid: str, email: str, name: Optional[str]) -> str:
        from app.core.security import create_access_token

        return create_access_token(subject=uid, extra={"email": email, "name": name})

    @staticmethod
    def _extract_firebase_error(body: dict[str, Any]) -> dict[str, str]:
        raw = body.get("error", {})
        message = raw.get("message", "")
        code = message.split(":", 1)[0].strip() if message else "UNKNOWN"
        return {"code": code, "message": message}
