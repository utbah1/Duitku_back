"""Firestore repository for transaction documents."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

from google.cloud.firestore import Client

from app.core.firebase import get_db
from app.models.transaction import Transaction
from app.utils.validators import to_datetime


class TransactionRepository:
    """Data-access methods for the `transactions` collection.

    Every query is scoped by `user_id` to guarantee that a user can only ever
    touch their own transactions.
    """

    COLLECTION = "transactions"

    def __init__(self, db: Optional[Client] = None):
        self._db = db or get_db()

    def _collection(self):
        return self._db.collection(self.COLLECTION)

    @staticmethod
    def _to_doc(tid: str, data: dict[str, Any], user_id: str) -> Transaction:
        return Transaction.from_dict(tid, data, user_id=user_id)

    @staticmethod
    def _to_firestore_date(value: Any) -> Any:
        """Convert a ``datetime.date`` to a Firestore-compatible ``datetime``.

        Firestore's admin SDK cannot serialize ``datetime.date`` objects; it
        only accepts ``datetime.datetime``. We normalize to UTC midnight so the
        value round-trips consistently through :func:`to_datetime` on read.
        """
        if isinstance(value, date) and not isinstance(value, datetime):
            return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
        return value

    def create(self, data: dict[str, Any]) -> Transaction:
        """Create a transaction and return it with its generated id."""
        now = datetime.now(timezone.utc)
        payload = {
            **data,
            "date": self._to_firestore_date(data.get("date")),
            "created_at": now,
            "updated_at": now,
        }
        ref = self._collection().document()
        ref.set(payload)
        return self._to_doc(ref.id, payload, data["user_id"])

    def get_by_id(self, transaction_id: str, user_id: str) -> Optional[Transaction]:
        """Return a transaction by id, but only if it belongs to `user_id`."""
        ref = self._collection().document(transaction_id)
        doc = ref.get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data.get("user_id") != user_id:
            return None
        return self._to_doc(doc.id, data, user_id)

    def get_all(
        self,
        user_id: str,
        *,
        limit: int = 20,
        type: Optional[str] = None,
        category: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        search: Optional[str] = None,
    ) -> list[Transaction]:
        """Fetch transactions for a user with optional filters, newest first."""
        # We fetch by user_id only and filter/sort in Python to avoid
        # Firestore composite-index requirements (e.g. filtering/order combined
        # with a range or equality filter on another field).
        docs = self._collection().where("user_id", "==", user_id).stream()

        results: list[Transaction] = []
        for doc in docs:
            data = doc.to_dict()
            tx = self._to_doc(doc.id, data, user_id)
            if type in ("income", "expense") and tx.type != type:
                continue
            if category and tx.category != category:
                continue
            if not self._matches_filters(tx, month, year, search):
                continue
            results.append(tx)

        # Newest first by created_at, then by id for stable ordering.
        results.sort(
            key=lambda tx: (
                tx.created_at is None,
                tx.created_at,
                tx.id or "",
            ),
            reverse=True,
        )
        return results[:limit]

    def list_paginated(
        self,
        user_id: str,
        *,
        page: int = 1,
        limit: int = 20,
        type: Optional[str] = None,
        category: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Transaction], int]:
        """Return (page_items, total_count) respecting filters."""
        # Firestore lacks native pagination-with-total; we fetch the filtered
        # subset in memory for correctness. For a production scale you would
        # switch to cursor-based pagination.
        all_items = self.get_all(
            user_id,
            limit=1000,
            type=type,
            category=category,
            month=month,
            year=year,
            search=search,
        )
        total = len(all_items)
        start = (page - 1) * limit
        end = start + limit
        return all_items[start:end], total

    def update(
        self, transaction_id: str, user_id: str, data: dict[str, Any]
    ) -> Optional[Transaction]:
        """Patch a transaction only if it belongs to `user_id`."""
        ref = self._collection().document(transaction_id)
        doc = ref.get()
        if not doc.exists:
            return None
        existing = doc.to_dict()
        if existing.get("user_id") != user_id:
            return None
        payload = {
            **data,
            "date": self._to_firestore_date(data.get("date", existing.get("date"))),
            "updated_at": datetime.now(timezone.utc),
        }
        ref.update(payload)
        merged = {**existing, **payload}
        return self._to_doc(transaction_id, merged, user_id)

    def delete(self, transaction_id: str, user_id: str) -> bool:
        """Delete a transaction only if it belongs to `user_id`."""
        ref = self._collection().document(transaction_id)
        doc = ref.get()
        if not doc.exists:
            return False
        if doc.to_dict().get("user_id") != user_id:
            return False
        ref.delete()
        return True

    def get_by_type(self, user_id: str, type: str) -> list[Transaction]:
        """Return all transactions of a given type for a user."""
        results = []
        docs = self._collection().where("user_id", "==", user_id).stream()
        for d in docs:
            tx = self._to_doc(d.id, d.to_dict(), user_id)
            if tx.type == type:
                results.append(tx)
        return results

    def get_by_date_range(
        self, user_id: str, start: date, end: date
    ) -> list[Transaction]:
        """Return a user's transactions within [start, end] (inclusive)."""
        # Fetch all user transactions and filter in Python to avoid
        # Firestore composite-index requirements and type inconsistencies.
        docs = (
            self._collection()
            .where("user_id", "==", user_id)
            .stream()
        )
        results = []
        for d in docs:
            tx = self._to_doc(d.id, d.to_dict(), user_id)
            if tx.date is not None and start <= tx.date <= end:
                results.append(tx)
        return results

    def get_summary(
        self, user_id: str, start: Optional[date] = None, end: Optional[date] = None
    ) -> dict[str, Any]:
        """Return aggregate totals for a user (optionally date-bounded)."""
        docs = self._collection().where("user_id", "==", user_id).stream()
        total_income = 0.0
        total_expense = 0.0
        count = 0
        for doc in docs:
            data = doc.to_dict()
            tx_date = to_datetime(data.get("date"))
            if tx_date is not None:
                tx_date = tx_date.date()
            if start and tx_date and tx_date < start:
                continue
            if end and tx_date and tx_date > end:
                continue
            amount = float(data.get("amount") or 0)
            if data.get("type") == "income":
                total_income += amount
            elif data.get("type") == "expense":
                total_expense += amount
            count += 1
        return {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "transaction_count": count,
        }

    def get_category_summary(
        self, user_id: str, type: str = "expense"
    ) -> list[dict[str, Any]]:
        """Return per-category totals and percentages for a transaction type."""
        totals: dict[str, float] = {}
        docs = self._collection().where("user_id", "==", user_id).stream()
        for doc in docs:
            data = doc.to_dict()
            if data.get("type") != type:
                continue
            cat = data.get("category") or "Uncategorized"
            totals[cat] = totals.get(cat, 0.0) + float(data.get("amount") or 0)

        grand = sum(totals.values())
        result = []
        for cat, total in sorted(
            totals.items(), key=lambda kv: kv[1], reverse=True
        ):
            percentage = round((total / grand * 100), 1) if grand > 0 else 0.0
            result.append(
                {"category": cat, "total": round(total, 2), "percentage": percentage}
            )
        return result

    @staticmethod
    def _matches_filters(
        tx: Transaction,
        month: Optional[int],
        year: Optional[int],
        search: Optional[str],
    ) -> bool:
        if year is not None and tx.date is not None and tx.date.year != year:
            return False
        if month is not None and tx.date is not None and tx.date.month != month:
            return False
        if search:
            needle = search.lower()
            haystack = " ".join(
                [tx.title or "", tx.category or "", tx.note or ""]
            ).lower()
            if needle not in haystack:
                return False
        return True
