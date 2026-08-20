"""General backend API routes."""

from fastapi import APIRouter

from src.contracts.health import HealthResponse

# --------------------------------------------------------------------------------------------------
# Router
# --------------------------------------------------------------------------------------------------
router = APIRouter(tags=["General"])

# --------------------------------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------------------------------
@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Report that the backend is ready to serve clients."""
    return HealthResponse(status="ready")
