"""About-information loading and validation."""

import json
from typing import NotRequired, TypedDict

from src.gui.utils.resources import ABOUT_FILE_PATH

# --------------------------------------------------------------------------------------------------
# Data structures
# --------------------------------------------------------------------------------------------------
class DeveloperInfo(TypedDict):
    """Main developer contact information."""

    name: str
    email: str
# --------------------------------------------------------------------------------------------------
class InstitutionInfo(TypedDict):
    """Institution name, logo file name, and optional website URL."""

    name: str
    logo: str
    url: NotRequired[str]
# --------------------------------------------------------------------------------------------------
class AboutInfo(TypedDict):
    """Application authorship and institutional information."""

    main_developer: DeveloperInfo
    laboratory: InstitutionInfo
    university: InstitutionInfo

# --------------------------------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------------------------------
def get_about_info() -> AboutInfo:
    """Load the configured about information."""
    # Resolve the metadata file
    about_file_path = ABOUT_FILE_PATH
    # Load the typed information
    with about_file_path.open(encoding="utf-8") as about_file:
        about_info: AboutInfo = json.load(about_file)
    return about_info
