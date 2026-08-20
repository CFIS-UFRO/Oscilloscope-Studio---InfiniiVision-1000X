"""Asynchronous release-update checker for the Qt event loop."""

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot

from src.contracts.api.releases import ReleaseUpdateResponse
from src.frontend.clients.releases import get_latest_release_update
from src.utils.logging import logger

# --------------------------------------------------------------------------------------------------
# Worker
# --------------------------------------------------------------------------------------------------
class _ReleaseUpdateCheckWorker(QObject):
    """Request the latest release without blocking the Qt event loop."""

    succeeded = Signal(ReleaseUpdateResponse)
    failed = Signal(str)
    finished = Signal()

    @Slot()
    def run(self) -> None:
        try:
            release_update = get_latest_release_update()
        except Exception as exc:
            logger.exception("Could not check for updates")
            self.failed.emit(str(exc))
        else:
            self.succeeded.emit(release_update)
        finally:
            self.finished.emit()
# --------------------------------------------------------------------------------------------------
# Component
# --------------------------------------------------------------------------------------------------
class ReleaseUpdateChecker(QObject):
    """Manage asynchronous release checks and their worker-thread lifecycle."""

    succeeded = Signal(ReleaseUpdateResponse)
    failed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _ReleaseUpdateCheckWorker | None = None

    @property
    def is_running(self) -> bool:
        """Return whether a release check is currently running."""
        return self._thread is not None

    def start(self) -> bool:
        """Start a release check and return whether it was started."""
        if self.is_running:
            return False
        thread = QThread(self)
        worker = _ReleaseUpdateCheckWorker()
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

    @Slot(ReleaseUpdateResponse)
    def _handle_success(self, release_update: ReleaseUpdateResponse) -> None:
        self.succeeded.emit(release_update)

    @Slot(str)
    def _handle_failure(self, error_message: str) -> None:
        self.failed.emit(error_message)

    @Slot()
    def _finish(self) -> None:
        self._thread = None
        self._worker = None
