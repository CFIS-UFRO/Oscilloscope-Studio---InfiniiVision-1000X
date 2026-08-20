"""Application release and update API routes."""

from fastapi import APIRouter, HTTPException

from src.backend.services.releases import get_latest_release_update, stage_latest_release_update
from src.contracts.api.releases import (
    ReleaseStageResponse,
    ReleaseUpdateResponse,
)

# --------------------------------------------------------------------------------------------------
# Router
# --------------------------------------------------------------------------------------------------
router = APIRouter(prefix="/releases", tags=["Releases"])

# --------------------------------------------------------------------------------------------------
# Releases
# --------------------------------------------------------------------------------------------------
@router.get("/latest", response_model=ReleaseUpdateResponse)
def get_latest_release() -> ReleaseUpdateResponse:
    """Return the latest published application release."""
    try:
        return get_latest_release_update()
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
# --------------------------------------------------------------------------------------------------
@router.post("/latest/stage", response_model=ReleaseStageResponse)
def stage_latest_release() -> ReleaseStageResponse:
    """Prepare the latest application release for the external updater."""
    try:
        return stage_latest_release_update()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
