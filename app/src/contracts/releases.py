"""Application release and update contracts."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------------------------------
# Types
# --------------------------------------------------------------------------------------------------
SemanticVersion = Annotated[str, Field(pattern=r"^\d+\.\d+\.\d+$")]
Sha256Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]

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
    releases: list[ReleaseEntry]

    @property
    def is_update_available(self) -> bool:
        """Return whether the published release is newer than the installed version."""
        current_version = tuple(int(part) for part in self.current_version.split("."))
        latest_version = tuple(int(part) for part in self.latest_version.split("."))
        return latest_version > current_version
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
