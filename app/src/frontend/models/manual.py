"""Manual metadata model."""

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------------------------------
class Manual(BaseModel):
    """Indexed manual metadata."""

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    file: str = Field(min_length=1)
