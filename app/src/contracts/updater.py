"""External updater handoff contracts."""

from pydantic import BaseModel

from src.contracts.types import SemanticVersion, Sha256Digest

# --------------------------------------------------------------------------------------------------
# Handoff
# --------------------------------------------------------------------------------------------------
class PendingReleaseUpdate(BaseModel):
    """Validated handoff from the backend to the external update script."""

    version: SemanticVersion
    archive_name: str
    archive_sha256: Sha256Digest
