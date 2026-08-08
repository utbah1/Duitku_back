"""Dashboard business logic (scoped to the authenticated user)."""
from __future__ import annotations

from typing import Any

from app.repositories.transaction_repository import TransactionRepository


class DashboardService:
    """Computes aggregate dashboard data for a single user."""

    def __init__(self, repo: TransactionRepository):
        self.repo = repo

    def get_dashboard(self, user_id: str) -> dict[str, Any]:
        summary = self.repo.get_summary(user_id)
        total_income = summary["total_income"]
        total_expense = summary["total_expense"]

        # Recent transactions (newest first).
        recent = self.repo.get_all(user_id, limit=5)

        return {
            "total_balance": round(total_income - total_expense, 2),
            "total_income": total_income,
            "total_expense": total_expense,
            "transaction_count": summary["transaction_count"],
            "recent_transactions": recent,
        }
