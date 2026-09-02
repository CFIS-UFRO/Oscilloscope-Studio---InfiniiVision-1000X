"""Help-manual index loading and validation."""

from functools import lru_cache

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from src.gui.utils.resources import HELP_INDEX_FILE_PATH

# --------------------------------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------------------------------
class HelpManual(BaseModel):
    """Indexed help manual metadata."""

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    file: str = Field(min_length=1)

# --------------------------------------------------------------------------------------------------
# Manual index
# --------------------------------------------------------------------------------------------------
_HELP_MANUALS_ADAPTER = TypeAdapter(list[HelpManual])
# --------------------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_help_manuals() -> list[HelpManual]:
    """Load and validate the configured help manuals."""
    try:
        return _HELP_MANUALS_ADAPTER.validate_json(
            HELP_INDEX_FILE_PATH.read_text(encoding="utf-8")
        )
    except ValidationError as exc:
        raise ValueError(f"Invalid help index: {HELP_INDEX_FILE_PATH}") from exc
