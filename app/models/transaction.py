"""Firestore-backed transaction model."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional


@dataclass(slots=True)
class Transaction:
    """Represents a transaction document in Firestore `transactions/{id}`."""

    id: Optional[str]
    user_id: str
    title: str
    amount: float
    category: str
    type: str  # "income" | "expense"
    note: Optional[str] = None
    date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "title": self.title,
            "amount": self.amount,
            "category": self.category,
            "type": self.type,
            "note": self.note,
            "date": self.date,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(
        cls, tid: str, data: dict[str, Any], user_id: Optional[str] = None
    ) -> "Transaction":
        raw_date = data.get("date")
        if isinstance(raw_date, datetime):
            parsed_date = raw_date.date()
        elif isinstance(raw_date, date):
            parsed_date = raw_date
        else:
            parsed_date = None

        created = data.get("created_at")
        if isinstance(created, date) and not isinstance(created, datetime):
            created = datetime.combine(created, datetime.min.time())

        return cls(
            id=tid,
            user_id=data.get("user_id", user_id or ""),
            title=data.get("title", ""),
            amount=float(data.get("amount", 0) or 0),
            category=data.get("category", ""),
            type=data.get("type", "expense"),
            note=data.get("note"),
            date=parsed_date,
            created_at=created,
            updated_at=data.get("updated_at"),
        )

