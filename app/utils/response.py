"""Consistent API response helpers."""
from __future__ import annotations

from typing import Any, Optional

from fastapi.encoders import jsonable_encoder


def success_response(
    message: str = "Success",
    data: Any = None,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build a consistent success response body."""
    body: dict[str, Any] = {
        "success": True,
        "message": message,
        "data": jsonable_encoder(data, custom_encoder={}),
    }
    if extra:
        body.update(extra)
    return body


def error_response(
    message: str = "Something went wrong",
    data: Any = None,
) -> dict[str, Any]:
    """Build a consistent error response body."""
    return {
        "success": False,
        "message": message,
        "data": data,
    }
