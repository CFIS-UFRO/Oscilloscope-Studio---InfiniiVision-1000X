"""Application release and update contracts."""

from datetime import datetime

from pydantic import BaseModel

from src.contracts.types import SemanticVersion, Sha256Digest

# --------------------------------------------------------------------------------------------------
# Release metadata
# --------------------------------------------------------------------------------------------------
class ReleaseEntry(BaseModel):
    """Versioned release notes published with an application release."""

    version: SemanticVersion
    created_at_utc: datetime
    changes: list[str]
# --------------------------------------------------------------------------------------------------
class ReleaseHistory(BaseModel):
    """Ordered collection of published application releases."""

    releases: list[ReleaseEntry]
# --------------------------------------------------------------------------------------------------
class ReleaseMetadata(BaseModel):
    """Metadata published alongside an application release archive."""

    version: SemanticVersion
    archive_sha256: Sha256Digest
    created_at_utc: datetime
    releases: list[ReleaseEntry]

# --------------------------------------------------------------------------------------------------
# API
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

# --------------------------------------------------------------------------------------------------
# Updater handoff
# --------------------------------------------------------------------------------------------------
class PendingReleaseUpdate(BaseModel):
    """Validated handoff from the backend to the external update script."""

    version: SemanticVersion
    archive_name: str
    archive_sha256: Sha256Digest
