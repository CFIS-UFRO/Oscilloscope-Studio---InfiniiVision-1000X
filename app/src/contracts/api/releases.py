"""Application release and update API contracts."""

from pydantic import BaseModel

from src.contracts.artifacts.releases import ReleaseEntry
from src.contracts.types import SemanticVersion

# --------------------------------------------------------------------------------------------------
# Responses
# --------------------------------------------------------------------------------------------------
class ReleaseUpdateResponse(BaseModel):
    """Latest published release compared with the installed application version."""

    current_version: SemanticVersion
    latest_version: SemanticVersion
    is_update_available: bool
    is_git_repository: bool
    releases: list[ReleaseEntry]
# --------------------------------------------------------------------------------------------------
class ReleaseStageResponse(BaseModel):
    """Confirm that an application update is ready for the external updater."""

    version: SemanticVersion
