"""Transaction endpoints (all require authentication)."""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.config import settings
from app.core.dependencies import CurrentUserDep
from app.core.firebase import get_db
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import (
    TransactionCreate,
    TransactionListResponse,
    TransactionOut,
    TransactionUpdate,
)
from app.services.transaction_service import TransactionService
from app.utils.response import success_response

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def get_transaction_service() -> TransactionService:
    return TransactionService(TransactionRepository(get_db()))


TransactionServiceDep = Annotated[TransactionService, Depends(get_transaction_service)]


def _tx_out(tx) -> dict:
    return {
        "id": tx.id,
        "user_id": tx.user_id,
        "title": tx.title,
        "amount": tx.amount,
        "category": tx.category,
        "type": tx.type,
        "note": tx.note,
        "date": tx.date.isoformat() if tx.date else None,
        "created_at": (
            tx.created_at.isoformat() if tx.created_at else None
        ),
        "updated_at": (
            tx.updated_at.isoformat() if tx.updated_at else None
        ),
    }


@router.get("", response_model=TransactionListResponse, summary="List transactions")
async def list_transactions(
    current_user: CurrentUserDep,
    service: TransactionServiceDep,
    page: int = Query(1, ge=1),
    limit: int = Query(settings.FIRESTORE_PAGE_LIMIT, ge=1, le=settings.FIRESTORE_MAX_PAGE_LIMIT),
    type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
):
    items, total = service.list(
        current_user.uid,
        page=page,
        limit=limit,
        type=type,
        category=category,
        month=month,
        year=year,
        search=search,
    )
    total_pages = (total + limit - 1) // limit if total else 0
    return success_response(
        "Transactions fetched successfully",
        [_tx_out(t) for t in items],
        extra={
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
            }
        },
    )


@router.get("/{transaction_id}", response_model=TransactionOut, summary="Get a transaction")
async def get_transaction(
    transaction_id: str,
    current_user: CurrentUserDep,
    service: TransactionServiceDep,
):
    tx = service.get(transaction_id, current_user.uid)
    return _tx_out(tx)


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED, summary="Create a transaction")
async def create_transaction(
    payload: TransactionCreate,
    current_user: CurrentUserDep,
    service: TransactionServiceDep,
):
    tx = service.create(
        current_user.uid,
        payload.model_dump(exclude_unset=True),
    )
    return _tx_out(tx)


@router.put("/{transaction_id}", response_model=TransactionOut, summary="Update a transaction")
async def update_transaction(
    transaction_id: str,
    payload: TransactionUpdate,
    current_user: CurrentUserDep,
    service: TransactionServiceDep,
):
    tx = service.update(
        transaction_id,
        current_user.uid,
        payload.model_dump(exclude_unset=True),
    )
    return _tx_out(tx)


@router.delete("/{transaction_id}", status_code=status.HTTP_200_OK, summary="Delete a transaction")
async def delete_transaction(
    transaction_id: str,
    current_user: CurrentUserDep,
    service: TransactionServiceDep,
):
    service.delete(transaction_id, current_user.uid)
    return success_response("Transaction deleted successfully", None)
