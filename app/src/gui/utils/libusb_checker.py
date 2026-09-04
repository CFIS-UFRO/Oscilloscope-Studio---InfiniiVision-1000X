"""Asynchronous libusb-availability check for the GUI event loop."""

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot

from src.core.logging import logger
from src.core.usb import is_libusb_available

# --------------------------------------------------------------------------------------------------
# Availability check worker
# --------------------------------------------------------------------------------------------------
class _LibusbCheckWorker(QObject):
    """Resolve libusb availability without blocking the Qt event loop."""

    succeeded = Signal(bool)
    failed = Signal(str)
    finished = Signal()

    @Slot()
    def run(self) -> None:
        try:
            available = is_libusb_available()
        except Exception as exc:
            logger.exception("Could not check libusb availability")
            self.failed.emit(str(exc))
        else:
            self.succeeded.emit(available)
        finally:
            self.finished.emit()
# --------------------------------------------------------------------------------------------------
class LibusbChecker(QObject):
    """Manage asynchronous libusb availability checks and their worker-thread lifecycle."""

    succeeded = Signal(bool)
    failed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _LibusbCheckWorker | None = None

    @property
    def is_running(self) -> bool:
        """Return whether an availability check is currently running."""
        return self._thread is not None

    def start(self) -> bool:
        """Start an availability check and return whether it was started."""
        if self.is_running:
            return False
        thread = QThread(self)
        worker = _LibusbCheckWorker()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(
            self._handle_success,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.failed.connect(
            self._handle_failure,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.destroyed.connect(self._finish)
        self._thread = thread
        self._worker = worker
        thread.start()
        return True

    @Slot(bool)
    def _handle_success(self, available: bool) -> None:
        self.succeeded.emit(available)

    @Slot(str)
    def _handle_failure(self, error_message: str) -> None:
        self.failed.emit(error_message)

    @Slot()
    def _finish(self) -> None:
        self._thread = None
        self._worker = None
