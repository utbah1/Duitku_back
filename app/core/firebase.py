"""Centralized Firebase Admin SDK initialization and Firestore client."""
import json
import os
from typing import Optional

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore as _firestore_module
from google.api_core.exceptions import GoogleAPICallError

from app.core.config import settings


class FirebaseNotConfiguredError(RuntimeError):
    """Raised when Firebase admin credentials are not available."""


def _build_credentials() -> Optional[credentials.Certificate]:
    """Build admin credentials from file or environment variables.

    Priority:
      1. A service account JSON file (default: serviceAccountKey.json) if present.
      2. Environment variables FIREBASE_PROJECT_ID / FIREBASE_CLIENT_EMAIL /
         FIREBASE_PRIVATE_KEY.
    Returns None when no usable credential is found.
    """
    key_path = settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH

    # 1. Try the service account file.
    if os.path.exists(key_path):
        try:
            with open(key_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if payload.get("type") == "service_account":
                return credentials.Certificate(payload)
        except (ValueError, KeyError, OSError):
            pass
        except Exception:
            pass

    # 2. Try environment variables.
    if settings.FIREBASE_CLIENT_EMAIL and settings.FIREBASE_PRIVATE_KEY:
        private_key = settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n")
        return credentials.Certificate(
            {
                "type": "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "private_key": private_key,
                "client_email": settings.FIREBASE_CLIENT_EMAIL,
                "client_id": settings.FIREBASE_CLIENT_ID,
            }
        )

    return None


default_app: Optional[firebase_admin.App] = None
_db = None


def init_firebase() -> None:
    """Initialize Firebase Admin SDK once and reuse the app/client."""
    global default_app, _db

    if default_app is not None:
        return

    creds = _build_credentials()
    if creds is None:
        raise FirebaseNotConfiguredError(
            "Firebase Admin credentials not configured. Set "
            "`FIREBASE_SERVICE_ACCOUNT_KEY_PATH` (service account JSON file) "
            "or `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, "
            "`FIREBASE_PRIVATE_KEY` environment variables."
        )

    default_app = firebase_admin.initialize_app(
        creds,
        options={"projectId": settings.FIREBASE_PROJECT_ID},
    )
    _db = _firestore_module.client(app=default_app)


def get_db():
    """Return the singleton Firestore client. Initialize Firebase if needed."""
    if _db is None or default_app is None:
        init_firebase()
    if _db is None:
        raise FirebaseNotConfiguredError("Firestore client is not initialized.")
    return _db


def is_firebase_ready() -> bool:
    """Return True if Firebase Admin has been initialized successfully."""
    return default_app is not None and _db is not None


def get_firestore_client():
    """Firestore client dependency for FastAPI (alias for get_db)."""
    return get_db()


def is_data_corruption_exc(exc: Exception) -> bool:
    """Return True if the exception is a known cloud / Firestore error."""
    return isinstance(exc, GoogleAPICallError)
