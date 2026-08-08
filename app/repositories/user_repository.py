"""Firestore repository for user documents."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from google.cloud.firestore import Client

from app.core.firebase import get_db
from app.models.user import UserProfile


class UserRepository:
    """Data-access methods for the `users` collection."""

    COLLECTION = "users"

    def __init__(self, db: Optional[Client] = None):
        self._db = db or get_db()

    def _collection(self):
        return self._db.collection(self.COLLECTION)

    def create(self, uid: str, email: str, name: Optional[str] = None) -> UserProfile:
        """Create a user document and return the created profile."""
        now = datetime.now(timezone.utc)
        data = {
            "uid": uid,
            "email": email,
            "name": name,
            "photo_url": None,
            "created_at": now,
        }
        self._collection().document(uid).set(data)
        return UserProfile.from_dict(uid, data)

    def get_by_id(self, uid: str) -> Optional[UserProfile]:
        """Return a user profile by uid, or None if not found."""
        doc = self._collection().document(uid).get()
        if not doc.exists:
            return None
        return UserProfile.from_dict(doc.id, doc.to_dict())

    def update(self, uid: str, data: dict[str, Any]) -> Optional[UserProfile]:
        """Update a user document and return the updated profile."""
        ref = self._collection().document(uid)
        doc = ref.get()
        if not doc.exists:
            return None
        ref.update(data)
        updated = ref.get().to_dict()
        return UserProfile.from_dict(uid, updated)

    def delete(self, uid: str) -> bool:
        """Delete a user document. Returns True if it existed."""
        ref = self._collection().document(uid)
        doc = ref.get()
        if not doc.exists:
            return False
        ref.delete()
        return True

    def upsert(self, uid: str, email: str, name: Optional[str] = None) -> UserProfile:
        """Create the user if it doesn't exist, otherwise return existing."""
        existing = self.get_by_id(uid)
        if existing:
            return existing
        return self.create(uid, email, name)
