"""Reusable validated API value types."""

from typing import Annotated

from pydantic import Field

# --------------------------------------------------------------------------------------------------
# Types
# --------------------------------------------------------------------------------------------------
SemanticVersion = Annotated[str, Field(pattern=r"^\d+\.\d+\.\d+$")]
Sha256Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
