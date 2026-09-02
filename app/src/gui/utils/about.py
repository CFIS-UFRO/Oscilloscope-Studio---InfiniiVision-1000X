"""About-information loading and validation."""

from pydantic import BaseModel, ValidationError

from src.gui.utils.resources import ABOUT_FILE_PATH

# --------------------------------------------------------------------------------------------------
# Data structures
# --------------------------------------------------------------------------------------------------
class DeveloperInfo(BaseModel):
    """Main developer contact information."""

    name: str
    email: str
# --------------------------------------------------------------------------------------------------
class InstitutionInfo(BaseModel):
    """Institution name, logo file name, and optional website URL."""

    name: str
    logo: str
    url: str | None = None
# --------------------------------------------------------------------------------------------------
class AboutInfo(BaseModel):
    """Application authorship and institutional information."""

    main_developer: DeveloperInfo
    laboratory: InstitutionInfo
    university: InstitutionInfo

# --------------------------------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------------------------------
def get_about_info() -> AboutInfo:
    """Load and validate the configured about information."""
    try:
        return AboutInfo.model_validate_json(ABOUT_FILE_PATH.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise ValueError(f"Invalid about information: {ABOUT_FILE_PATH}") from exc
