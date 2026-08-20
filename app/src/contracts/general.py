"""General application API contracts."""

from pydantic import BaseModel

from src.contracts.types import SemanticVersion

# --------------------------------------------------------------------------------------------------
# Responses
# --------------------------------------------------------------------------------------------------
class ApplicationInfoResponse(BaseModel):
    """Report general information about the running application."""

    version: SemanticVersion
