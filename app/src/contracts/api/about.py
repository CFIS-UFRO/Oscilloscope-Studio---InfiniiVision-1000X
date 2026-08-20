"""Application About-information API contracts."""

from pydantic import BaseModel

# --------------------------------------------------------------------------------------------------
# Responses
# --------------------------------------------------------------------------------------------------
class DeveloperInfo(BaseModel):
    """Main developer contact information."""

    name: str
    email: str
# --------------------------------------------------------------------------------------------------
class InstitutionLogos(BaseModel):
    """Backend image paths for the light and dark logo variants."""

    light: str
    dark: str
# --------------------------------------------------------------------------------------------------
class InstitutionInfo(BaseModel):
    """Institution name, logo resources, and optional website URL."""

    name: str
    logos: InstitutionLogos
    url: str | None = None
# --------------------------------------------------------------------------------------------------
class AboutResponse(BaseModel):
    """Application authorship and institutional information."""

    main_developer: DeveloperInfo
    laboratory: InstitutionInfo
    university: InstitutionInfo
