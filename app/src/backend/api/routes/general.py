"""General backend API routes."""

from fastapi import APIRouter

from src.contracts.api.general import ApplicationInfoResponse
from src.contracts.api.health import HealthResponse
from src.utils.versions import get_pyproject_version

# --------------------------------------------------------------------------------------------------
# Router
# --------------------------------------------------------------------------------------------------
router = APIRouter(tags=["General"])

# --------------------------------------------------------------------------------------------------
# Application information
# --------------------------------------------------------------------------------------------------
@router.get("/info", response_model=ApplicationInfoResponse)
async def get_application_info() -> ApplicationInfoResponse:
    """Return general information about the running application."""
    return ApplicationInfoResponse(version=get_pyproject_version())
# --------------------------------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------------------------------
@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Report that the backend is ready to serve clients."""
    return HealthResponse(status="ready")
