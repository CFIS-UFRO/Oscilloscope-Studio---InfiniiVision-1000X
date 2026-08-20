"""Validated manual collection model."""

from pydantic import RootModel

from src.frontend.models.manual import Manual

# --------------------------------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------------------------------
class ManualCollection(RootModel[list[Manual]]):
    """Validated collection of indexed manuals."""
