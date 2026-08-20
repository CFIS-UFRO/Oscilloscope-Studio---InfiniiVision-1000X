"""Centralized filesystem paths used by the backend."""

from pathlib import Path

from src.utils.paths import get_src_dir_path

# --------------------------------------------------------------------------------------------------
# Directories
# --------------------------------------------------------------------------------------------------
BACKEND_DIR: Path = get_src_dir_path() / "backend"

# --------------------------------------------------------------------------------------------------
# Getters
# --------------------------------------------------------------------------------------------------
def get_backend_dir_path() -> Path:
    """Return the backend source directory."""
    return BACKEND_DIR
