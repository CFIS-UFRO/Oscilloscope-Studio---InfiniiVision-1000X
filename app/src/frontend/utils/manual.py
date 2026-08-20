"""Manual-index loading and validation."""

from functools import lru_cache

from src.frontend.models.manual import MANUALS_ADAPTER, Manual
from src.frontend.utils.paths import HELP_INDEX_FILE_PATH

# --------------------------------------------------------------------------------------------------
# Manual index
# --------------------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_manuals() -> list[Manual]:
    """Load and validate the configured manuals."""
    return MANUALS_ADAPTER.validate_json(HELP_INDEX_FILE_PATH.read_bytes())
