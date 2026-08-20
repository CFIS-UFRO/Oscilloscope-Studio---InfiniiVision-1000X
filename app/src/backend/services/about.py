"""About-information service."""

from functools import lru_cache
from pathlib import Path

from src.backend.utils.paths import ABOUT_FILE_PATH, LOGOS_DIR
from src.contracts.api.about import AboutResponse

# --------------------------------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_about_info() -> AboutResponse:
    """Load and validate the configured About information."""
    return AboutResponse.model_validate_json(ABOUT_FILE_PATH.read_text(encoding="utf-8"))
# --------------------------------------------------------------------------------------------------
def get_about_logo_file_path(logo_name: str, theme: str) -> Path:
    """Return the file path for a theme-specific institution logo."""
    return LOGOS_DIR / f"{logo_name}_{theme}.png"
