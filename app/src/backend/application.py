"""FastAPI backend application factory."""

from fastapi import FastAPI

from src.backend.api.router import api_router
from src.config import APP_DESCRIPTION, APP_NAME

# --------------------------------------------------------------------------------------------------
# Application factory
# --------------------------------------------------------------------------------------------------
def create_application() -> FastAPI:
    """Create and configure the backend API application."""
    application = FastAPI(
        title=f"{APP_NAME} Backend",
        description=APP_DESCRIPTION,
    )
    application.include_router(api_router)
    return application

# --------------------------------------------------------------------------------------------------
# ASGI application
# --------------------------------------------------------------------------------------------------
application = create_application()
