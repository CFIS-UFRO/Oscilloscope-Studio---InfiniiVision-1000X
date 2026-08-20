"""About-information service."""

from functools import lru_cache

from src.backend.utils.paths import ABOUT_FILE_PATH
from src.contracts.api.about import AboutResponse

# --------------------------------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_about_info() -> AboutResponse:
    """Load and validate the configured About information."""
    return AboutResponse.model_validate_json(ABOUT_FILE_PATH.read_text(encoding="utf-8"))
