"""Dashboard endpoint."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUserDep
from app.core.firebase import get_db
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService
from app.utils.response import success_response

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_dashboard_service() -> DashboardService:
    return DashboardService(TransactionRepository(get_db()))


DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]


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
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
        "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
    }


@router.get("", response_model=DashboardResponse, summary="Get user dashboard summary")
async def get_dashboard(
    current_user: CurrentUserDep,
    service: DashboardServiceDep,
):
    data = service.get_dashboard(current_user.uid)
    data["recent_transactions"] = [_tx_out(t) for t in data["recent_transactions"]]
    return success_response("Dashboard fetched successfully", data)
