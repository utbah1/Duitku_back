"""Report schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SummaryReport(BaseModel):
    total_income: float
    total_expense: float
    balance: float
    transaction_count: int


class DailyReportItem(BaseModel):
    date: str
    day: str  # Nama hari: Senin, Selasa, dst.
    income: float
    expense: float


class WeeklyReport(BaseModel):
    period: str
    days: list[DailyReportItem]


class MonthlyReport(BaseModel):
    year: int
    month: int
    total_income: float
    total_expense: float
    balance: float
    transaction_count: int


class CategoryReportItem(BaseModel):
    category: str
    total: float
    percentage: float


class CategoryReport(BaseModel):
    data: list[CategoryReportItem]
