"""Versioned backend API router."""

from fastapi import APIRouter

from src.backend.api.routes.general import router as general_router

# --------------------------------------------------------------------------------------------------
# API router
# --------------------------------------------------------------------------------------------------
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(general_router)
