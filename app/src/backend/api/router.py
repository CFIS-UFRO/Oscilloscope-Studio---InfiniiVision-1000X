"""Versioned backend API router."""

from fastapi import APIRouter

from src.backend.api.routes.about import router as about_router
from src.backend.api.routes.general import router as general_router
from src.backend.api.routes.releases import router as releases_router

# --------------------------------------------------------------------------------------------------
# API router
# --------------------------------------------------------------------------------------------------
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(about_router)
api_router.include_router(general_router)
api_router.include_router(releases_router)
