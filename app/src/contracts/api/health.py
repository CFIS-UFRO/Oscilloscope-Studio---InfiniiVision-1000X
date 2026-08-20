"""Backend health-check API contracts."""

from typing import Literal

from pydantic import BaseModel

# --------------------------------------------------------------------------------------------------
# Responses
# --------------------------------------------------------------------------------------------------
class HealthResponse(BaseModel):
    """Report whether the backend is ready to serve clients."""

    status: Literal["ready"]
