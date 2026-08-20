"""Manual-index loading and validation."""

from functools import lru_cache

from src.frontend.models.manuals import Manuals
from src.frontend.utils.paths import HELP_INDEX_FILE_PATH

# --------------------------------------------------------------------------------------------------
# Manual index
# --------------------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_manuals() -> Manuals:
    """Load and validate the configured manuals."""
    return Manuals.model_validate_json(HELP_INDEX_FILE_PATH.read_bytes())
