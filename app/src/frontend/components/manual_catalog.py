"""Manual catalog loading and search indexing."""

import re
from functools import lru_cache
from pathlib import Path

from src.frontend.models.manuals import Manuals
from src.frontend.utils.paths import HELP_INDEX_FILE_PATH

# --------------------------------------------------------------------------------------------------
# Catalog
# --------------------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_manuals() -> Manuals:
    """Load and validate the configured manuals."""
    return Manuals.model_validate_json(HELP_INDEX_FILE_PATH.read_bytes())
# --------------------------------------------------------------------------------------------------
def get_manual_search_text(manual_file_path: Path) -> str:
    """Return normalized searchable text extracted from a manual HTML file."""
    try:
        raw_html = manual_file_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    plain_text = re.sub(r"<[^>]+>", "", raw_html)
    return re.sub(r"\s+", " ", plain_text).strip()
