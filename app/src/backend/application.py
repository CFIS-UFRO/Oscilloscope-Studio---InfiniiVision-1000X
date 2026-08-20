"""FastAPI backend application factory."""

import time
from uuid import uuid4

from fastapi import FastAPI, Request

from src.backend.api.router import api_router
from src.backend.utils.time import format_duration
from src.config import APP_DESCRIPTION, APP_NAME
from src.utils.logging import logger

# --------------------------------------------------------------------------------------------------
# Application factory
# --------------------------------------------------------------------------------------------------
def create_application() -> FastAPI:
    """Create and configure the backend API application."""
    application = FastAPI(
        title=f"{APP_NAME} Backend",
        description=APP_DESCRIPTION,
    )

    @application.middleware("http")
    async def log_request(request: Request, call_next):
        request_id = uuid4().hex[:8]
        method = request.method
        path = request.url.path
        started_at = time.perf_counter()
        logger.info(f"[{request_id}] --> {method} {path}")
        try:
            response = await call_next(request)
        except Exception:
            elapsed = format_duration(time.perf_counter() - started_at)
            logger.exception(f"[{request_id}] <-- {method} {path} failed after {elapsed}")
            raise
        elapsed = format_duration(time.perf_counter() - started_at)
        logger.info(f"[{request_id}] <-- {method} {path} {response.status_code} in {elapsed}")
        return response

    application.include_router(api_router)
    return application

# --------------------------------------------------------------------------------------------------
# ASGI application
# --------------------------------------------------------------------------------------------------
application = create_application()
