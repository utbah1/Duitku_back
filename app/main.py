"""DuitKu Backend - FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.firebase import FirebaseNotConfiguredError, init_firebase
from app.routers import auth, dashboard, reports, transactions, users
from app.utils.exceptions import AppError
from app.utils.response import error_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Attempt to initialize Firebase once at startup. If credentials are
    # missing, the app still boots and /health reports it; guarded endpoints
    # will surface a clear 503.
    try:
        init_firebase()
        logger.info("Firebase Admin initialized successfully.")
    except FirebaseNotConfiguredError as exc:
        logger.warning("Firebase not initialized: %s", exc)
    yield


app = FastAPI(
    title="DuitKu Backend API",
    description="REST API backend for the DuitKu personal finance app.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.message),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = {}
    for err in exc.errors():
        loc = err.get("loc", ())
        field = str(loc[-1]) if loc else "body"
        errors.setdefault(field, err.get("msg", "Invalid value"))
    return JSONResponse(
        status_code=422,
        content=error_response("Validation error", errors),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if settings.ENVIRONMENT == "development":
        detail = f"Internal server error: {exc}"
    else:
        detail = "Internal server error"
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content=error_response(detail),
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"], summary="Health check")
async def health():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
    }


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
API_V1_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(users.router, prefix=API_V1_PREFIX)
app.include_router(transactions.router, prefix=API_V1_PREFIX)
app.include_router(dashboard.router, prefix=API_V1_PREFIX)
app.include_router(reports.router, prefix=API_V1_PREFIX)
