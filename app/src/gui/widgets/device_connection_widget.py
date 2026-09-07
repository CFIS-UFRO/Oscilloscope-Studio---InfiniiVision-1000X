"""Keysight device selector with a VISA connect/disconnect control."""

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.visa import VisaDeviceInfo, VisaSession
from src.gui.utils.visa_connection import VisaConnector, VisaDiscoveryChecker
from src.gui.widgets.status_dot_widget import StatusDotWidget

# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------
REFRESH_INTERVAL_MS = 5_000
NO_DEVICE_PLACEHOLDER_TEXT = "No device connected"

# --------------------------------------------------------------------------------------------------
# Widget
# --------------------------------------------------------------------------------------------------
class DeviceConnectionWidget(QGroupBox):
    """Select a connected Keysight device and open/close a VISA session to it."""

    status_message = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Device Connection", parent)
        self._state = "idle"
        self._session: VisaSession | None = None
        self._connected_resource: str | None = None
        self._remembered_resource: str | None = None
        self._pending_resource_string: str | None = None
        self._pending_disconnect_is_lost = False
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        # Device selector
        self._device_combo = QComboBox(self)
        self._device_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._device_combo.currentIndexChanged.connect(self._handle_selection_changed)
        layout.addWidget(self._device_combo)
        # Connect/disconnect control, with a small status dot indicating the connection state
        control_row = QHBoxLayout()
        control_row.setSpacing(8)
        self._connect_button = QPushButton(self)
        self._connect_button.clicked.connect(self._handle_button_clicked)
        control_row.addWidget(self._connect_button, 1)
        self._status_indicator = StatusDotWidget(parent=self)
        control_row.addWidget(self._status_indicator, 0)
        layout.addLayout(control_row)
        # Background workers
        self._discovery_checker = VisaDiscoveryChecker(self)
        self._discovery_checker.succeeded.connect(self._handle_discovery_succeeded)
        self._discovery_checker.failed.connect(self._handle_discovery_failed)
        self._connector = VisaConnector(self)
        self._connector.connect_succeeded.connect(self._handle_connect_succeeded)
        self._connector.connect_failed.connect(self._handle_connect_failed)
        self._connector.disconnect_succeeded.connect(self._handle_disconnect_succeeded)
        # Periodic refresh
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(REFRESH_INTERVAL_MS)
        self._refresh_timer.timeout.connect(self._handle_refresh_tick)
        self._refresh_timer.start()
        self._set_idle_style()
        # Seed the placeholder synchronously: the first real discovery result only arrives once
        # the background thread finishes, which would otherwise leave the combo blank at startup.
        self._populate_devices([])
        self._handle_refresh_tick()

    # ----------------------------------------------------------------------------------------------
    # Button and status dot state
    # ----------------------------------------------------------------------------------------------
    def _set_idle_style(self) -> None:
        self._state = "idle"
        self._connect_button.setText("Start Communication")
        self._device_combo.setEnabled(True)
        self._status_indicator.set_status(self._state)
        self._update_connect_button_enabled()

    def _set_connecting_style(self) -> None:
        self._state = "connecting"
        self._connect_button.setText("Connecting...")
        self._device_combo.setEnabled(False)
        self._connect_button.setEnabled(False)
        self._status_indicator.set_status(self._state)

    def _set_connected_style(self) -> None:
        self._state = "connected"
        self._connect_button.setText("Stop Communication")
        self._device_combo.setEnabled(False)
        self._connect_button.setEnabled(True)
        self._status_indicator.set_status(self._state)

    def _set_disconnecting_style(self) -> None:
        self._state = "disconnecting"
        self._connect_button.setText("Disconnecting...")
        self._connect_button.setEnabled(False)
        self._status_indicator.set_status(self._state)

    def _update_connect_button_enabled(self) -> None:
        if self._state != "idle":
            return
        self._connect_button.setEnabled(self._device_combo.currentData() is not None)

    # ----------------------------------------------------------------------------------------------
    # User actions
    # ----------------------------------------------------------------------------------------------
    def _handle_button_clicked(self) -> None:
        if self._state == "idle":
            self._start_connect()
        elif self._state == "connected":
            self._start_disconnect(is_lost=False)

    def _handle_selection_changed(self, _index: int) -> None:
        # Only reached for a genuine user selection: programmatic reselects run with signals blocked.
        self._remembered_resource = None
        self._update_connect_button_enabled()

    # ----------------------------------------------------------------------------------------------
    # Connect / disconnect
    # ----------------------------------------------------------------------------------------------
    def _start_connect(self) -> None:
        device: VisaDeviceInfo | None = self._device_combo.currentData()
        if device is None or self._connector.is_running:
            return
        self._pending_resource_string = device.resource_string
        self._set_connecting_style()
        self._connector.connect_to(device.resource_string)

    def _handle_connect_succeeded(self, session: VisaSession, identification: str) -> None:
        self._session = session
        self._connected_resource = self._pending_resource_string
        self._remembered_resource = self._pending_resource_string
        self._pending_resource_string = None
        self._set_connected_style()
        self.status_message.emit("INFO", f"Connected: {identification}")

    def _handle_connect_failed(self, error_message: str) -> None:
        self._pending_resource_string = None
        self._set_idle_style()
        self.status_message.emit("ERROR", f"Could not connect to device: {error_message}")

    def _start_disconnect(self, is_lost: bool) -> None:
        if self._session is None or self._connector.is_running:
            return
        self._pending_disconnect_is_lost = is_lost
        self._set_disconnecting_style()
        self._connector.disconnect_from(self._session)

    def _handle_disconnect_succeeded(self) -> None:
        self._session = None
        self._connected_resource = None
        was_lost = self._pending_disconnect_is_lost
        self._pending_disconnect_is_lost = False
        self._set_idle_style()
        if was_lost:
            self.status_message.emit("WARNING", "Device disconnected unexpectedly")
        else:
            self.status_message.emit("INFO", "Disconnected")
        self._handle_refresh_tick()

    # ----------------------------------------------------------------------------------------------
    # Periodic discovery
    # ----------------------------------------------------------------------------------------------
    def _handle_refresh_tick(self) -> None:
        if self._discovery_checker.is_running:
            return
        self._discovery_checker.start()

    def _handle_discovery_succeeded(self, devices: list[VisaDeviceInfo]) -> None:
        if self._connected_resource is not None:
            still_present = any(device.resource_string == self._connected_resource for device in devices)
            if not still_present:
                self._start_disconnect(is_lost=True)
                return
        if self._state != "idle":
            return
        self._populate_devices(devices)

    def _handle_discovery_failed(self, _error_message: str) -> None:
        # A failed listing attempt (e.g. transient backend hiccup) is not treated as proof the
        # connected device is gone; only a successful listing that omits it triggers disconnect.
        pass

    def _populate_devices(self, devices: list[VisaDeviceInfo]) -> None:
        remembered_resource = self._remembered_resource
        self._device_combo.blockSignals(True)
        self._device_combo.clear()
        if not devices:
            self._device_combo.addItem(NO_DEVICE_PLACEHOLDER_TEXT, None)
        for device in devices:
            self._device_combo.addItem(
                f"VID {device.vendor_id_hex} | PID {device.product_id_hex} | "
                f"SN {device.serial_number or 'N/A'}",
                device,
            )
        if remembered_resource is not None:
            index = self._find_index_by_resource(remembered_resource)
            if index is not None:
                self._device_combo.setCurrentIndex(index)
        self._device_combo.blockSignals(False)
        self._update_connect_button_enabled()

    def _find_index_by_resource(self, resource_string: str) -> int | None:
        for index in range(self._device_combo.count()):
            device: VisaDeviceInfo | None = self._device_combo.itemData(index)
            if device is not None and device.resource_string == resource_string:
                return index
        return None
