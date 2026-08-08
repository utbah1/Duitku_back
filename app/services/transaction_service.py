"""Transaction business logic. Always scoped to the authenticated user."""
from __future__ import annotations

from typing import Any, Optional

from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository
from app.utils.exceptions import NotFoundError, TRANSACTION_NOT_FOUND_DETAIL


class TransactionService:
    """Encapsulates transaction operations and ownership enforcement."""

    def __init__(self, repo: TransactionRepository):
        self.repo = repo

    def create(self, user_id: str, data: dict[str, Any]) -> Transaction:
        # user_id ALWAYS comes from the authenticated token, never the body.
        payload = {**data, "user_id": user_id}
        return self.repo.create(payload)

    def get(self, transaction_id: str, user_id: str) -> Transaction:
        tx = self.repo.get_by_id(transaction_id, user_id)
        if tx is None:
            raise NotFoundError(TRANSACTION_NOT_FOUND_DETAIL)
        return tx

    def list(
        self,
        user_id: str,
        *,
        page: int,
        limit: int,
        type: Optional[str],
        category: Optional[str],
        month: Optional[int],
        year: Optional[int],
        search: Optional[str],
    ) -> tuple[list[Transaction], int]:
        items, total = self.repo.list_paginated(
            user_id,
            page=page,
            limit=limit,
            type=type,
            category=category,
            month=month,
            year=year,
            search=search,
        )
        return items, total

    def update(
        self, transaction_id: str, user_id: str, data: dict[str, Any]
    ) -> Transaction:
        updated = self.repo.update(transaction_id, user_id, data)
        if updated is None:
            raise NotFoundError(TRANSACTION_NOT_FOUND_DETAIL)
        return updated

    def delete(self, transaction_id: str, user_id: str) -> None:
        if not self.repo.delete(transaction_id, user_id):
            raise NotFoundError(TRANSACTION_NOT_FOUND_DETAIL)
