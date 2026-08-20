"""Application About-information API routes."""

from typing import Literal

from fastapi import APIRouter
from fastapi.responses import FileResponse

from src.backend.services.about import get_about_info, get_about_logo_file_path
from src.contracts.api.about import AboutResponse

# --------------------------------------------------------------------------------------------------
# Router
# --------------------------------------------------------------------------------------------------
router = APIRouter(tags=["About"])

# --------------------------------------------------------------------------------------------------
# About
# --------------------------------------------------------------------------------------------------
@router.get("/about", response_model=AboutResponse)
async def get_about() -> AboutResponse:
    """Return application authorship and institutional information."""
    return get_about_info()
# --------------------------------------------------------------------------------------------------
@router.get("/about/logos/{logo_name}/{theme}", response_class=FileResponse)
async def get_about_logo(
    logo_name: Literal["cfis", "ufro"],
    theme: Literal["light", "dark"],
) -> FileResponse:
    """Return a theme-specific institution logo."""
    return FileResponse(
        get_about_logo_file_path(logo_name, theme),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )
