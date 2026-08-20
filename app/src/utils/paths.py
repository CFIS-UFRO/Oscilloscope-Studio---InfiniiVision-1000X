"""Centralized filesystem paths used by the application."""

from pathlib import Path

# --------------------------------------------------------------------------------------------------
# Directories
# --------------------------------------------------------------------------------------------------
APP_DIR: Path = Path(__file__).resolve().parents[2]
PROJECT_DIR: Path = APP_DIR.parent
SRC_DIR: Path = APP_DIR / "src"
LOGS_DIR: Path = APP_DIR / "logs"
USER_DATA_DIR: Path = APP_DIR / "usr"
TMP_DIR: Path = APP_DIR / "tmp"

# --------------------------------------------------------------------------------------------------
# Files
# --------------------------------------------------------------------------------------------------
PYPROJECT_FILE_PATH: Path = APP_DIR / "pyproject.toml"
UV_LOCK_FILE_PATH: Path = APP_DIR / "uv.lock"
RELEASES_FILE_PATH: Path = APP_DIR / "releases.json"
