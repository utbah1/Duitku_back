"""Validation helpers beyond Pydantic field constraints."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional


def iso_date(value: Optional[date]) -> Optional[str]:
    """Return an ISO yyyy-mm-dd string for a date, or None."""
    if value is None:
        return None
    return value.isoformat()


def normalize_date_str(value: Optional[str]) -> Optional[str]:
    """Normalize an optional date string into yyyy-mm-dd or None."""
    if not value:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except (ValueError, TypeError):
        return None


def parse_year_month(year: Optional[int], month: Optional[int]) -> tuple[int, int]:
    """Validate and return a year/month pair, defaulting to today."""
    today = date.today()
    y = year or today.year
    m = month or today.month
    if not (1 <= m <= 12):
        raise ValueError("month must be between 1 and 12.")
    if not (2000 <= y <= 2100):
        raise ValueError("year is out of range.")
    return y, m


def start_of_week(d: date) -> date:
    """Return the Monday of the week containing d."""
    return d - timedelta(days=d.weekday())


def end_of_week(d: date) -> date:
    """Return the Sunday of the week containing d."""
    return start_of_week(d) + timedelta(days=6)


def month_bounds(year: int, month: int) -> tuple[date, date]:
    """Return (first_day, last_day) of the given month."""
    first = date(year, month, 1)
    if month == 12:
        nxt = date(year + 1, 1, 1)
    else:
        nxt = date(year, month + 1, 1)
    return first, nxt - timedelta(days=1)


def to_datetime(value) -> Optional[datetime]:
    """Coerce a Firestore value into a datetime if possible."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None
