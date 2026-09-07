"""Shared identity constants and base model for Keysight instruments."""

from pydantic import BaseModel

# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------
KEYSIGHT_VENDOR_ID = 0x2A8D

# --------------------------------------------------------------------------------------------------
# Data models
# --------------------------------------------------------------------------------------------------
class KeysightDeviceInfo(BaseModel):
    """A Keysight device identified by its USB vendor and product IDs."""

    vendor_id: int
    product_id: int
    serial_number: str | None = None

    @property
    def vendor_id_hex(self) -> str:
        """Return the vendor ID as a lowercase four-digit hex string."""
        return f"{self.vendor_id:04x}"

    @property
    def product_id_hex(self) -> str:
        """Return the product ID as a lowercase four-digit hex string."""
        return f"{self.product_id:04x}"
