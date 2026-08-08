"""Financial report business logic (scoped to the authenticated user)."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

from app.core.config import settings
from app.repositories.transaction_repository import TransactionRepository
from app.utils.validators import month_bounds, parse_year_month, start_of_week

WEEKDAY_NAMES = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


class ReportService:
    """Produces summary, weekly, monthly, and category reports."""

    def __init__(self, repo: TransactionRepository):
        self.repo = repo

    def summary(self, user_id: str) -> dict[str, Any]:
        s = self.repo.get_summary(user_id)
        return {
            "total_income": s["total_income"],
            "total_expense": s["total_expense"],
            "balance": round(s["total_income"] - s["total_expense"], 2),
            "transaction_count": s["transaction_count"],
        }

    def weekly(self, user_id: str, week_offset: int = 0) -> dict[str, Any]:
        today = date.today()
        monday = start_of_week(today) + timedelta(weeks=week_offset)
        sunday = monday + timedelta(days=6)

        txs = self.repo.get_by_date_range(user_id, monday, sunday)

        days: list[dict[str, Any]] = []
        for day_index in range(7):
            day = monday + timedelta(days=day_index)
            income = 0.0
            expense = 0.0
            for tx in txs:
                if tx.date != day:
                    continue
                if tx.type == "income":
                    income += tx.amount
                elif tx.type == "expense":
                    expense += tx.amount
            days.append(
                {
                    "date": day.isoformat(),
                    "day": WEEKDAY_NAMES[day_index],
                    "income": round(income, 2),
                    "expense": round(expense, 2),
                }
            )

        return {
            "period": f"{monday.isoformat()} to {sunday.isoformat()}",
            "days": days,
        }

    def monthly(
        self, user_id: str, year: Optional[int], month: Optional[int]
    ) -> dict[str, Any]:
        y, m = parse_year_month(year, month)
        first, last = month_bounds(y, m)
        s = self.repo.get_summary(user_id, start=first, end=last)
        return {
            "year": y,
            "month": m,
            "total_income": s["total_income"],
            "total_expense": s["total_expense"],
            "balance": round(s["total_income"] - s["total_expense"], 2),
            "transaction_count": s["transaction_count"],
        }

    def categories(self, user_id: str, type: str = "expense") -> list[dict[str, Any]]:
        return self.repo.get_category_summary(user_id, type=type)
