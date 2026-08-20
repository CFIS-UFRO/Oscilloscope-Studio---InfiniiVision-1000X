"""Centralized filesystem paths used by the backend."""

from pathlib import Path

from src.utils.paths import APP_DIR, SRC_DIR

# --------------------------------------------------------------------------------------------------
# Directories
# --------------------------------------------------------------------------------------------------
BACKEND_DIR: Path = SRC_DIR / "backend"
TMP_DIR: Path = APP_DIR / "tmp"
