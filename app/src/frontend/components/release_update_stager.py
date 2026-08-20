"""Asynchronous release-update stager for the Qt event loop."""

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot

from src.contracts.api.releases import ReleaseStageResponse
from src.frontend.clients.releases import stage_latest_release_update
from src.utils.logging import logger

# --------------------------------------------------------------------------------------------------
# Worker
# --------------------------------------------------------------------------------------------------
class _ReleaseUpdateStageWorker(QObject):
    """Request update preparation without blocking the Qt event loop."""

    succeeded = Signal(ReleaseStageResponse)
    failed = Signal(str)
    finished = Signal()

    @Slot()
    def run(self) -> None:
        try:
            staged_update = stage_latest_release_update()
        except Exception as exc:
            logger.exception("Could not prepare release update")
            self.failed.emit(str(exc))
        else:
            self.succeeded.emit(staged_update)
        finally:
            self.finished.emit()
# --------------------------------------------------------------------------------------------------
# Component
# --------------------------------------------------------------------------------------------------
class ReleaseUpdateStager(QObject):
    """Manage asynchronous update staging and its worker-thread lifecycle."""

    succeeded = Signal(ReleaseStageResponse)
    failed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _ReleaseUpdateStageWorker | None = None

    @property
    def is_running(self) -> bool:
        """Return whether update preparation is currently running."""
        return self._thread is not None

    def start(self) -> bool:
        """Start update preparation and return whether it was started."""
        if self.is_running:
            return False
        thread = QThread(self)
        worker = _ReleaseUpdateStageWorker()
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

    @Slot(ReleaseStageResponse)
    def _handle_success(self, staged_update: ReleaseStageResponse) -> None:
        self.succeeded.emit(staged_update)

    @Slot(str)
    def _handle_failure(self, error_message: str) -> None:
        self.failed.emit(error_message)

    @Slot()
    def _finish(self) -> None:
        self._thread = None
        self._worker = None
