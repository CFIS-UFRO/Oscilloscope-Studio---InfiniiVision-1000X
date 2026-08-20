"""Manual data models and validation."""

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

# --------------------------------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------------------------------
class Manual(BaseModel):
    """Indexed manual metadata."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    file: str = Field(min_length=1)

# --------------------------------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------------------------------
MANUALS_ADAPTER = TypeAdapter(list[Manual])
