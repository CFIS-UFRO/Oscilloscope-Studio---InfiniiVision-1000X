"""Published release artifact contracts."""

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
