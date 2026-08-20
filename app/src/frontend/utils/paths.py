"""Centralized filesystem paths used by the frontend."""

from pathlib import Path

from src.utils.paths import SRC_DIR

# --------------------------------------------------------------------------------------------------
# Directories
# --------------------------------------------------------------------------------------------------
FRONTEND_DIR: Path = SRC_DIR / "frontend"
ASSETS_DIR: Path = FRONTEND_DIR / "assets"
HELP_DIR: Path = ASSETS_DIR / "help"
ICONS_DIR: Path = ASSETS_DIR / "icons"
LOGOS_DIR: Path = ASSETS_DIR / "logos"

# --------------------------------------------------------------------------------------------------
# Files
# --------------------------------------------------------------------------------------------------
ICON_FILE_PATH: Path = ASSETS_DIR / "icon.png"
ABOUT_FILE_PATH: Path = ASSETS_DIR / "about.json"
HELP_INDEX_FILE_PATH: Path = HELP_DIR / "index.json"
HELP_BLACK_ICON_FILE_PATH: Path = ICONS_DIR / "help_black.svg"
HELP_WHITE_ICON_FILE_PATH: Path = ICONS_DIR / "help_white.svg"
EXTERNAL_LINK_BLACK_ICON_FILE_PATH: Path = ICONS_DIR / "external_link_black.svg"
EXTERNAL_LINK_WHITE_ICON_FILE_PATH: Path = ICONS_DIR / "external_link_white.svg"

# --------------------------------------------------------------------------------------------------
# Path resolution
# --------------------------------------------------------------------------------------------------
def get_help_icon_file_path(is_dark_mode: bool = False) -> Path:
    """Return the help icon path for the current color theme."""
    return HELP_WHITE_ICON_FILE_PATH if is_dark_mode else HELP_BLACK_ICON_FILE_PATH
# --------------------------------------------------------------------------------------------------
def get_external_link_icon_file_path(is_dark_mode: bool = False) -> Path:
    """Return the external-link icon path for the current color theme."""
    return EXTERNAL_LINK_WHITE_ICON_FILE_PATH if is_dark_mode else EXTERNAL_LINK_BLACK_ICON_FILE_PATH
# --------------------------------------------------------------------------------------------------
def get_logo_file_path(file_name: str, is_dark_mode: bool = False) -> Path:
    """Return the theme-specific logo path for a base file name."""
    base_file_path = Path(file_name)
    if not file_name or base_file_path.name != file_name:
        raise ValueError(f"Logo path must contain only a file name: {file_name}")
    theme_suffix = "dark" if is_dark_mode else "light"
    return LOGOS_DIR / f"{base_file_path.stem}_{theme_suffix}{base_file_path.suffix}"
