"""Transaction schemas."""
from __future__ import annotations

import datetime as _dt
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

TransactionType = Literal["income", "expense"]


class TransactionBase(BaseModel):
    """Common transaction fields. `user_id` is never accepted from the client."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0, description="Must be greater than 0.")
    category: str = Field(..., min_length=1, max_length=100)
    type: TransactionType = "expense"
    note: Optional[str] = Field(None, max_length=1000)
    date: Optional[_dt.date] = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be empty.")
        return v

    @field_validator("category")
    @classmethod
    def category_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("category must not be empty.")
        return v


class TransactionCreate(TransactionBase):
    """Payload for POST /api/v1/transactions."""


class TransactionUpdate(BaseModel):
    """Payload for PUT /api/v1/transactions/{id}.

    All fields optional; only provided fields are updated.
    """

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[TransactionType] = None
    note: Optional[str] = Field(None, max_length=1000)
    date: Optional[_dt.date] = None

    @field_validator("title", "category")
    @classmethod
    def not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("field must not be empty.")
        return v


class TransactionOut(TransactionBase):
    """Transaction response object."""

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    user_id: str
    created_at: Optional[_dt.datetime] = None
    updated_at: Optional[_dt.datetime] = None


class TransactionListResponse(BaseModel):
    """Paginated transaction list response."""

    success: bool = True
    message: str = "Transactions fetched successfully"
    data: list[TransactionOut]
    pagination: dict
