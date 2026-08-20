"""Centralized filesystem paths used by the backend."""

from pathlib import Path

from src.utils.paths import APP_DIR, SRC_DIR

# --------------------------------------------------------------------------------------------------
# Directories
# --------------------------------------------------------------------------------------------------
BACKEND_DIR: Path = SRC_DIR / "backend"
ASSETS_DIR: Path = BACKEND_DIR / "assets"
LOGOS_DIR: Path = ASSETS_DIR / "logos"
TMP_DIR: Path = APP_DIR / "tmp"

# --------------------------------------------------------------------------------------------------
# Files
# --------------------------------------------------------------------------------------------------
ABOUT_FILE_PATH: Path = ASSETS_DIR / "about.json"
PENDING_UPDATE_FILE_PATH: Path = TMP_DIR / "pending_update.json"
