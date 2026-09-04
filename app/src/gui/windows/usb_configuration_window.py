"""USB configuration dialog with OS-specific libusb setup instructions."""

import sys

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.logging import logger
from src.core.usb import UsbDeviceInfo, build_udev_install_command, list_keysight_usb_devices
from src.gui.utils.libusb_checker import LibusbChecker
from src.gui.widgets.badge_widget import BadgeWidget
from src.gui.widgets.close_button_widget import CloseButtonWidget
from src.gui.widgets.copy_text_widget import CopyTextWidget
from src.gui.widgets.url_widget import UrlWidget

# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------
ZADIG_URL = "https://zadig.akeo.ie/"
LIBUSB_RELEASES_URL = "https://github.com/libusb/libusb/releases"
SEVEN_ZIP_URL = "https://www.7-zip.org/"
HOMEBREW_URL = "https://brew.sh"

# --------------------------------------------------------------------------------------------------
# Dialog
# --------------------------------------------------------------------------------------------------
class UsbConfigurationWindow(QDialog):
    """Walk through OS-specific USB/libusb setup steps for the oscilloscope."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("USB Configuration")
        self.resize(640, 520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        # Setup tabs
        self._windows_tab = _WindowsSetupTab(self)
        self._linux_tab = _LinuxSetupTab(self)
        self._macos_tab = _MacosSetupTab(self)
        self._all_tabs = (self._windows_tab, self._linux_tab, self._macos_tab)
        self._tabs = QTabWidget(self)
        for tab, name in zip(self._all_tabs, ("Windows", "Linux", "macOS")):
            tab.reload_libusb_requested.connect(self._check_libusb)
            self._tabs.addTab(tab, name)
        self._tabs.setCurrentIndex(self._current_platform_tab_index())
        layout.addWidget(self._tabs, 1)
        layout.addWidget(CloseButtonWidget(self))
        # Background libusb check
        self._libusb_checker = LibusbChecker(self)
        self._libusb_checker.succeeded.connect(self._handle_check_success)
        self._libusb_checker.failed.connect(self._handle_check_failure)

    @staticmethod
    def _current_platform_tab_index() -> int:
        if sys.platform == "win32":
            return 0
        if sys.platform == "linux":
            return 1
        return 2

    def show_window(self) -> None:
        """Show, raise, activate the dialog, and (re)check libusb availability."""
        logger.info("Opening USB configuration window")
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        if sys.platform != "darwin":
            self.activateWindow()
        self._check_libusb()

    def _check_libusb(self) -> None:
        if self._libusb_checker.is_running:
            return
        for tab in self._all_tabs:
            tab.set_libusb_status("checking")
        self._libusb_checker.start()

    @Slot(bool)
    def _handle_check_success(self, available: bool) -> None:
        status = "available" if available else "unavailable"
        for tab in self._all_tabs:
            tab.set_libusb_status(status)
        if available:
            self._linux_tab.refresh_devices()

    @Slot(str)
    def _handle_check_failure(self, error_message: str) -> None:
        logger.warning(f"Could not check libusb availability: {error_message}")
        for tab in self._all_tabs:
            tab.set_libusb_status("unavailable")

# --------------------------------------------------------------------------------------------------
# Shared step widgets
# --------------------------------------------------------------------------------------------------
def _step_text(step_number: int, text: str) -> str:
    """Format a top-level step's number prefix, shared by labels and interactive widgets."""
    return f"{step_number}. {text}"
# --------------------------------------------------------------------------------------------------
def _substep_text(letter: str, text: str) -> str:
    """Format an indented substep's letter prefix, shared by labels and interactive widgets."""
    return f"      {letter}. {text}"
# --------------------------------------------------------------------------------------------------
def _create_step_label(step_number: int, text: str, parent: QWidget) -> QLabel:
    label = QLabel(_step_text(step_number, text), parent)
    label.setWordWrap(False)
    return label
# --------------------------------------------------------------------------------------------------
def _create_substep_label(letter: str, text: str, parent: QWidget) -> QLabel:
    label = QLabel(_substep_text(letter, text), parent)
    label.setWordWrap(False)
    return label
# --------------------------------------------------------------------------------------------------
def _create_libusb_setup_block(parent: QWidget) -> tuple[QVBoxLayout, BadgeWidget, QPushButton]:
    """Build the always-visible step-1 block: intro, status, and reload (callers append substeps)."""
    block_layout = QVBoxLayout()
    block_layout.setSpacing(4)
    block_layout.addWidget(
        _create_step_label(
            1,
            "libusb is distributed with the application. If it is not found, "
            "follow the steps below to install it manually.",
            parent,
        )
    )
    status_row = QHBoxLayout()
    badge = BadgeWidget("Checking libusb...", "gray", parent)
    badge.setFixedWidth(220)
    status_row.addWidget(badge)
    reload_button = QPushButton("Reload", parent)
    status_row.addWidget(reload_button)
    status_row.addStretch(1)
    block_layout.addLayout(status_row)
    block_layout.addWidget(QLabel("Steps:", parent))
    return block_layout, badge, reload_button
# --------------------------------------------------------------------------------------------------
def _set_libusb_badge_status(badge: BadgeWidget, status: str) -> None:
    if status == "available":
        badge.setText("libusb detected")
        badge.set_color("green")
    elif status == "unavailable":
        badge.setText("libusb not found")
        badge.set_color("red")
    else:
        badge.setText("Checking libusb...")
        badge.set_color("gray")

# --------------------------------------------------------------------------------------------------
# Windows tab
# --------------------------------------------------------------------------------------------------
class _WindowsSetupTab(QWidget):
    """Zadig-based WinUSB driver setup steps for Windows."""

    reload_libusb_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        libusb_block, self._badge, reload_button = _create_libusb_setup_block(self)
        reload_button.clicked.connect(self.reload_libusb_requested.emit)
        libusb_block.addWidget(
            UrlWidget(_substep_text("a", "Go to the libusb releases page:"), LIBUSB_RELEASES_URL, self)
        )
        libusb_block.addWidget(_create_substep_label("b", "Download the latest release archive (.7z).", self))
        libusb_block.addWidget(
            UrlWidget(_substep_text("c", "Extract it with 7-Zip:"), SEVEN_ZIP_URL, self)
        )
        libusb_block.addWidget(
            _create_substep_label(
                "d",
                "Copy VS2019\\MS64\\dll\\libusb-1.0.dll (or MS32 for 32-bit Windows) "
                "next to the application's executable.",
                self,
            )
        )
        layout.addLayout(libusb_block)
        # Zadig download step
        layout.addWidget(UrlWidget(_step_text(2, "Download Zadig:"), ZADIG_URL, self))
        for step_number, text in (
            (3, "Connect the oscilloscope. If using a USB hub, connect the hub first, then the oscilloscope."),
            (4, "Open Zadig as Administrator (right-click the executable, \"Run as administrator\")."),
            (5, "If using a USB hub, deselect Options → Ignore Hubs or Composite Parents."),
            (6, "Go to Options → List All Devices."),
            (7, "Select the oscilloscope (Keysight vendor ID 2A8D) and choose the WinUSB driver as target."),
            (8, "Click Install Driver (or Replace Driver)."),
            (9, "Always reconnect the oscilloscope to the same USB port afterward."),
        ):
            layout.addWidget(_create_step_label(step_number, text, self))
        layout.addStretch(1)

    def set_libusb_status(self, status: str) -> None:
        """Update the libusb status badge."""
        _set_libusb_badge_status(self._badge, status)

# --------------------------------------------------------------------------------------------------
# Linux tab
# --------------------------------------------------------------------------------------------------
class _LinuxSetupTab(QWidget):
    """udev rule setup steps for Linux."""

    reload_libusb_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._selected_device: UsbDeviceInfo | None = None
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        libusb_block, self._badge, reload_button = _create_libusb_setup_block(self)
        reload_button.clicked.connect(self.reload_libusb_requested.emit)
        libusb_block.addWidget(_create_substep_label("a", "Open a terminal.", self))
        libusb_block.addWidget(
            CopyTextWidget(_substep_text("b", "Debian/Ubuntu:"), "sudo apt install libusb-1.0-0", self)
        )
        libusb_block.addWidget(
            CopyTextWidget(_substep_text("c", "Fedora:"), "sudo dnf install libusb1", self)
        )
        libusb_block.addWidget(
            CopyTextWidget(_substep_text("d", "Arch:"), "sudo pacman -S libusb", self)
        )
        layout.addLayout(libusb_block)
        # Device selector
        device_row = QHBoxLayout()
        device_row.addWidget(_create_step_label(2, "Select the connected Keysight oscilloscope:", self))
        self._device_combo = QComboBox(self)
        self._device_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._device_combo.currentIndexChanged.connect(self._handle_selection_changed)
        device_row.addWidget(self._device_combo, 1)
        refresh_button = QPushButton("Refresh", self)
        refresh_button.clicked.connect(self.refresh_devices)
        device_row.addWidget(refresh_button)
        layout.addLayout(device_row)
        # udev rule and install command
        layout.addWidget(
            _create_step_label(
                3,
                "Copy this command, paste it in a terminal, run it, then unplug and replug the oscilloscope:",
                self,
            )
        )
        self._command_label = QLabel("Select a device above", self)
        self._command_label.setWordWrap(True)
        self._command_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._command_label.setStyleSheet(
            "font-family: monospace; background-color: palette(base); padding: 8px; "
            "border-radius: 6px;"
        )
        layout.addWidget(self._command_label)
        self._copy_command_button = QPushButton("Copy command", self)
        self._copy_command_button.setEnabled(False)
        self._copy_command_button.clicked.connect(self._copy_command)
        layout.addWidget(self._copy_command_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)

    def set_libusb_status(self, status: str) -> None:
        """Update the libusb status badge."""
        _set_libusb_badge_status(self._badge, status)

    def refresh_devices(self) -> None:
        """Reload the list of connected Keysight USB devices."""
        self._device_combo.blockSignals(True)
        self._device_combo.clear()
        try:
            devices = list_keysight_usb_devices()
        except Exception as exc:
            logger.warning(f"Could not list Keysight USB devices: {exc}")
            self._device_combo.addItem("Could not list USB devices.")
            devices = []
        if not devices:
            if self._device_combo.count() == 0:
                self._device_combo.addItem("No Keysight oscilloscope detected")
        else:
            for device in devices:
                self._device_combo.addItem(
                    f"VID {device.vendor_id_hex} | PID {device.product_id_hex} | "
                    f"{device.product_name or 'Unknown model'} | SN {device.serial_number or 'N/A'}",
                    device,
                )
        self._device_combo.blockSignals(False)
        self._handle_selection_changed(self._device_combo.currentIndex())

    def _handle_selection_changed(self, index: int) -> None:
        self._selected_device = self._device_combo.itemData(index)
        self._update_command()

    def _update_command(self) -> None:
        if self._selected_device is None:
            self._command_label.setText("Select a device above")
            self._copy_command_button.setEnabled(False)
            return
        command = build_udev_install_command(
            self._selected_device.vendor_id, self._selected_device.product_id
        )
        self._command_label.setText(command)
        self._copy_command_button.setEnabled(True)

    def _copy_command(self) -> None:
        if self._selected_device is None:
            return
        command = build_udev_install_command(
            self._selected_device.vendor_id, self._selected_device.product_id
        )
        QApplication.clipboard().setText(command)

# --------------------------------------------------------------------------------------------------
# macOS tab
# --------------------------------------------------------------------------------------------------
class _MacosSetupTab(QWidget):
    """Homebrew-based libusb setup steps for macOS."""

    reload_libusb_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        libusb_block, self._badge, reload_button = _create_libusb_setup_block(self)
        reload_button.clicked.connect(self.reload_libusb_requested.emit)
        libusb_block.addWidget(_create_substep_label("a", "Open a terminal.", self))
        libusb_block.addWidget(
            UrlWidget(_substep_text("b", "Install Homebrew if you don't have it:"), HOMEBREW_URL, self)
        )
        libusb_block.addWidget(CopyTextWidget(_substep_text("c", "Run:"), "brew install libusb", self))
        layout.addLayout(libusb_block)
        layout.addStretch(1)

    def set_libusb_status(self, status: str) -> None:
        """Update the libusb status badge."""
        _set_libusb_badge_status(self._badge, status)
