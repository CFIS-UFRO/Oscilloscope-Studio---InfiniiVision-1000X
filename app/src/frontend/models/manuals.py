"""Manual data models and collection validation."""

from pydantic import BaseModel, Field, RootModel

# --------------------------------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------------------------------
class Manual(BaseModel):
    """Indexed manual metadata."""

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    file: str = Field(min_length=1)
# --------------------------------------------------------------------------------------------------
class Manuals(RootModel[list[Manual]]):
    """Validated collection of indexed manuals."""
