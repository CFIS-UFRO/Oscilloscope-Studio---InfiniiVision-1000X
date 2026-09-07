"""Asynchronous VISA discovery and connection helpers for the GUI event loop."""

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot

from src.core.logging import logger
from src.core.visa import KeysightVisaDeviceInfo, VisaSession, list_keysight_visa_resources

# --------------------------------------------------------------------------------------------------
# Discovery worker
# --------------------------------------------------------------------------------------------------
class _VisaDiscoveryWorker(QObject):
    """Resolve the connected Keysight VISA resources without blocking the Qt event loop."""

    succeeded = Signal(list)
    failed = Signal(str)
    finished = Signal()

    @Slot()
    def run(self) -> None:
        try:
            devices = list_keysight_visa_resources()
        except Exception as exc:
            logger.exception("Could not list Keysight VISA resources")
            self.failed.emit(str(exc))
        else:
            self.succeeded.emit(devices)
        finally:
            self.finished.emit()
# --------------------------------------------------------------------------------------------------
class VisaDiscoveryChecker(QObject):
    """Manage asynchronous VISA discovery checks and their worker-thread lifecycle."""

    succeeded = Signal(list)
    failed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _VisaDiscoveryWorker | None = None

    @property
    def is_running(self) -> bool:
        """Return whether a discovery check is currently running."""
        return self._thread is not None

    def start(self) -> bool:
        """Start a discovery check and return whether it was started."""
        if self.is_running:
            return False
        thread = QThread(self)
        worker = _VisaDiscoveryWorker()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(self._handle_success, Qt.ConnectionType.QueuedConnection)
        worker.failed.connect(self._handle_failure, Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.destroyed.connect(self._finish)
        self._thread = thread
        self._worker = worker
        thread.start()
        return True

    @Slot(list)
    def _handle_success(self, devices: list[KeysightVisaDeviceInfo]) -> None:
        self.succeeded.emit(devices)

    @Slot(str)
    def _handle_failure(self, error_message: str) -> None:
        self.failed.emit(error_message)

    @Slot()
    def _finish(self) -> None:
        self._thread = None
        self._worker = None

# --------------------------------------------------------------------------------------------------
# Connect/disconnect worker
# --------------------------------------------------------------------------------------------------
class _VisaConnectorWorker(QObject):
    """Common shape for the connect and disconnect workers: both signal completion the same way."""

    finished = Signal()
# --------------------------------------------------------------------------------------------------
class _VisaConnectWorker(_VisaConnectorWorker):
    """Open a VISA session to a resource without blocking the Qt event loop."""

    succeeded = Signal(object, str)
    failed = Signal(str)

    def __init__(self, resource_string: str) -> None:
        super().__init__()
        self._resource_string = resource_string

    @Slot()
    def run(self) -> None:
        session = VisaSession(self._resource_string)
        try:
            identification = session.open()
        except Exception as exc:
            logger.exception(f"Could not open VISA session to {self._resource_string}")
            self.failed.emit(str(exc))
        else:
            self.succeeded.emit(session, identification)
        finally:
            self.finished.emit()
# --------------------------------------------------------------------------------------------------
class _VisaDisconnectWorker(_VisaConnectorWorker):
    """Close a VISA session without blocking the Qt event loop."""

    succeeded = Signal()

    def __init__(self, session: VisaSession) -> None:
        super().__init__()
        self._session = session

    @Slot()
    def run(self) -> None:
        self._session.close()
        self.succeeded.emit()
        self.finished.emit()
# --------------------------------------------------------------------------------------------------
class VisaConnector(QObject):
    """Manage asynchronous VISA connect/disconnect requests and their worker-thread lifecycle."""

    connect_succeeded = Signal(object, str)
    connect_failed = Signal(str)
    disconnect_succeeded = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _VisaConnectorWorker | None = None

    @property
    def is_running(self) -> bool:
        """Return whether a connect or disconnect request is currently running."""
        return self._thread is not None

    def connect_to(self, resource_string: str) -> bool:
        """Start opening a VISA session to the given resource and return whether it was started."""
        if self.is_running:
            return False
        thread = QThread(self)
        worker = _VisaConnectWorker(resource_string)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(self._handle_connect_success, Qt.ConnectionType.QueuedConnection)
        worker.failed.connect(self._handle_connect_failure, Qt.ConnectionType.QueuedConnection)
        self._start_thread(thread, worker)
        return True

    def disconnect_from(self, session: VisaSession) -> bool:
        """Start closing the given VISA session and return whether it was started."""
        if self.is_running:
            return False
        thread = QThread(self)
        worker = _VisaDisconnectWorker(session)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(self._handle_disconnect_success, Qt.ConnectionType.QueuedConnection)
        self._start_thread(thread, worker)
        return True

    def _start_thread(self, thread: QThread, worker: _VisaConnectorWorker) -> None:
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.destroyed.connect(self._finish)
        self._thread = thread
        self._worker = worker
        thread.start()

    @Slot(object, str)
    def _handle_connect_success(self, session: VisaSession, identification: str) -> None:
        self.connect_succeeded.emit(session, identification)

    @Slot(str)
    def _handle_connect_failure(self, error_message: str) -> None:
        self.connect_failed.emit(error_message)

    @Slot()
    def _handle_disconnect_success(self) -> None:
        self.disconnect_succeeded.emit()

    @Slot()
    def _finish(self) -> None:
        self._thread = None
        self._worker = None
