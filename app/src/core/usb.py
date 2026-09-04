"""USB backend detection and Keysight device discovery over libusb."""

import usb.backend
import usb.backend.libusb1
import usb.core
import usb.util
from pydantic import BaseModel

import libusb_package

# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------
KEYSIGHT_VENDOR_ID = 0x2A8D
UDEV_RULES_FILE_PATH = "/etc/udev/rules.d/99-keysight-oscilloscope.rules"

# --------------------------------------------------------------------------------------------------
# Data models
# --------------------------------------------------------------------------------------------------
class UsbDeviceInfo(BaseModel):
    """A single USB device identified by vendor and product IDs."""

    vendor_id: int
    product_id: int
    product_name: str | None = None
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
# libusb backend
# --------------------------------------------------------------------------------------------------
def is_libusb_available() -> bool:
    """Return whether a working libusb backend can be loaded."""
    return _get_libusb_backend() is not None
# --------------------------------------------------------------------------------------------------
def _get_libusb_backend() -> usb.backend.IBackend | None:
    return usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)

# --------------------------------------------------------------------------------------------------
# Device discovery
# --------------------------------------------------------------------------------------------------
def list_keysight_usb_devices() -> list[UsbDeviceInfo]:
    """Return the Keysight USB devices currently connected to the computer."""
    backend = _get_libusb_backend()
    if backend is None:
        raise RuntimeError("No working libusb backend is available.")
    devices = usb.core.find(find_all=True, idVendor=KEYSIGHT_VENDOR_ID, backend=backend)
    if devices is None:
        return []
    device_infos = (_to_device_info(device) for device in devices)
    return [device_info for device_info in device_infos if device_info is not None]
# --------------------------------------------------------------------------------------------------
def _to_device_info(device: object) -> UsbDeviceInfo | None:
    vendor_id = getattr(device, "idVendor", None)
    product_id = getattr(device, "idProduct", None)
    if vendor_id is None or product_id is None:
        return None
    return UsbDeviceInfo(
        vendor_id=vendor_id,
        product_id=product_id,
        product_name=_read_string_descriptor(device, getattr(device, "iProduct", None)),
        serial_number=_read_string_descriptor(device, getattr(device, "iSerialNumber", None)),
    )
# --------------------------------------------------------------------------------------------------
def _read_string_descriptor(device: object, index: int | None) -> str | None:
    if not index:
        return None
    try:
        value = usb.util.get_string(device, index)
    except usb.core.USBError:
        return None
    # Discard garbled reads (e.g. a control transfer racing device enumeration)
    if value is not None and not value.isprintable():
        return None
    return value

# --------------------------------------------------------------------------------------------------
# Linux udev rule
# --------------------------------------------------------------------------------------------------
def build_udev_rule(vendor_id: int, product_id: int) -> str:
    """Return the udev rule line granting non-root USB access to a device."""
    return (
        f'SUBSYSTEM=="usb", ATTR{{idVendor}}=="{vendor_id:04x}", '
        f'ATTR{{idProduct}}=="{product_id:04x}", MODE="0666"'
    )
# --------------------------------------------------------------------------------------------------
def build_udev_install_command(vendor_id: int, product_id: int) -> str:
    """Return the shell command that installs and reloads the udev rule."""
    rule = build_udev_rule(vendor_id, product_id)
    return (
        f"echo '{rule}' | sudo tee {UDEV_RULES_FILE_PATH} "
        "&& sudo udevadm control --reload-rules && sudo udevadm trigger"
    )
