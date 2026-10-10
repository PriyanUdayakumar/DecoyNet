from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import DecoyNetError
from app.core.logging import CorrelationIdMiddleware, configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend API for IoT decoy event ingestion, detection, discovery, and dashboard data."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-Correlation-ID"],
)
app.add_middleware(CorrelationIdMiddleware)
app.include_router(api_router)


@app.exception_handler(DecoyNetError)
async def decoynet_error_handler(request: Request, exc: DecoyNetError) -> JSONResponse:
    logger.info("handled_error code=%s message=%s", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.status_code, content={"error": exc.code, "message": exc.message}
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unexpected_error path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": "Unexpected server error"},
    )
