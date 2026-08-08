"""Financial report endpoints."""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import CurrentUserDep
from app.core.firebase import get_db
from app.repositories.transaction_repository import TransactionRepository
from app.services.report_service import ReportService
from app.utils.response import success_response

router = APIRouter(prefix="/reports", tags=["Reports"])


def get_report_service() -> ReportService:
    return ReportService(TransactionRepository(get_db()))


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]


@router.get("/summary", summary="Financial summary")
async def summary(current_user: CurrentUserDep, service: ReportServiceDep):
    return success_response("Summary report fetched successfully", service.summary(current_user.uid))


@router.get("/weekly", summary="Weekly report")
async def weekly(
    current_user: CurrentUserDep,
    service: ReportServiceDep,
    week_offset: int = Query(0, ge=-52, le=52),
):
    return success_response("Weekly report fetched successfully", service.weekly(current_user.uid, week_offset))


@router.get("/monthly", summary="Monthly report")
async def monthly(
    current_user: CurrentUserDep,
    service: ReportServiceDep,
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
):
    return success_response("Monthly report fetched successfully", service.monthly(current_user.uid, year, month))


@router.get("/categories", summary="Category report")
async def categories(
    current_user: CurrentUserDep,
    service: ReportServiceDep,
    type: str = Query("expense"),
):
    return success_response(
        "Category report fetched successfully",
        service.categories(current_user.uid, type=type),
    )
