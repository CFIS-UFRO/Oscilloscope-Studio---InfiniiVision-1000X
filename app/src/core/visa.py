"""VISA resource discovery and instrument sessions for Keysight oscilloscopes."""

import warnings

import pyvisa
from pydantic import BaseModel

from src.core.logging import logger
from src.core.usb import KEYSIGHT_VENDOR_ID

# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------
VISA_TIMEOUT_MS = 5_000
IDENTIFICATION_QUERY = "*IDN?"

# --------------------------------------------------------------------------------------------------
# Silence pyvisa-py warnings about LAN instrument discovery (zeroconf/psutil): this application
# only ever talks to USB-connected Keysight devices, so those optional dependencies buy nothing.
# --------------------------------------------------------------------------------------------------
warnings.filterwarnings("ignore", message=r"TCPIP::hislip resource discovery.*", category=UserWarning)
warnings.filterwarnings("ignore", message=r"TCPIP:instr resource discovery.*", category=UserWarning)

# --------------------------------------------------------------------------------------------------
# Data models
# --------------------------------------------------------------------------------------------------
class VisaDeviceInfo(BaseModel):
    """A single VISA-addressable device identified by vendor and product IDs."""

    resource_string: str
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

# --------------------------------------------------------------------------------------------------
# Device discovery
# --------------------------------------------------------------------------------------------------
def list_keysight_visa_resources() -> list[VisaDeviceInfo]:
    """Return the Keysight VISA resources currently connected to the computer."""
    resource_manager = pyvisa.ResourceManager("@py")
    try:
        resource_strings = resource_manager.list_resources()
    finally:
        resource_manager.close()
    device_infos = (_to_device_info(resource_string) for resource_string in resource_strings)
    return [device_info for device_info in device_infos if device_info is not None]
# --------------------------------------------------------------------------------------------------
def _to_device_info(resource_string: str) -> VisaDeviceInfo | None:
    # USB INSTR resource strings look like "USB0::10893::6027::CN60100132::0::INSTR":
    #   [0] interface type + board number (e.g. "USB0")
    #   [1] vendor ID (decimal)
    #   [2] product ID (decimal)
    #   [3] serial number
    #   [4] USB interface number (optional, not always present)
    #   [-1] resource class, always "INSTR" here
    segments = resource_string.split("::")
    if len(segments) < 5 or not segments[0].upper().startswith("USB"):
        return None
    if segments[-1].upper() != "INSTR":
        return None
    try:
        # VISA resource strings encode vendor/model IDs in decimal (e.g. "10893", not "0x2A8D").
        # Passing base=0 makes int() auto-detect the base from the string itself, so this still
        # works unchanged if a backend ever returns a "0x"-prefixed value instead.
        vendor_id = int(segments[1], 0)
        product_id = int(segments[2], 0)
    except ValueError:
        return None
    if vendor_id != KEYSIGHT_VENDOR_ID:
        return None
    return VisaDeviceInfo(
        resource_string=resource_string,
        vendor_id=vendor_id,
        product_id=product_id,
        serial_number=segments[3] or None,
    )

# --------------------------------------------------------------------------------------------------
# Instrument sessions
# --------------------------------------------------------------------------------------------------
class VisaSession:
    """A VISA connection to an instrument, identified by its resource string."""

    def __init__(self, resource_string: str) -> None:
        self.resource_string = resource_string
        self.resource_manager: pyvisa.ResourceManager | None = None
        self.instrument: pyvisa.resources.MessageBasedResource | None = None

    def open(self) -> str:
        """Open the VISA session and confirm communication with an identification query."""
        resource_manager = pyvisa.ResourceManager("@py")
        try:
            instrument = resource_manager.open_resource(self.resource_string)
            if not isinstance(instrument, pyvisa.resources.MessageBasedResource):
                raise TypeError(f"Resource '{self.resource_string}' does not support message-based I/O.")
            instrument.timeout = VISA_TIMEOUT_MS
            identification = instrument.query(IDENTIFICATION_QUERY).strip()
        except Exception:
            resource_manager.close()
            raise
        self.resource_manager = resource_manager
        self.instrument = instrument
        logger.info(f"Opened VISA session to {self.resource_string}: {identification}")
        return identification

    def close(self) -> None:
        """Close this VISA session, logging but not raising on failure."""
        logger.info(f"Closing VISA session to {self.resource_string}")
        if self.instrument is not None:
            try:
                self.instrument.close()
            except Exception as exc:
                logger.warning(f"Could not close VISA instrument session: {exc}")
        if self.resource_manager is not None:
            try:
                self.resource_manager.close()
            except Exception as exc:
                logger.warning(f"Could not close VISA resource manager: {exc}")
