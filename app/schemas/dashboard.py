"""Dashboard schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.schemas.transaction import TransactionOut


class DashboardResponse(BaseModel):
    """Response for GET /api/v1/dashboard."""

    success: bool = True
    message: str = "Dashboard fetched successfully"
    data: "DashboardData"


class DashboardData(BaseModel):
    total_balance: float
    total_income: float
    total_expense: float
    transaction_count: int
    recent_transactions: list[TransactionOut]
