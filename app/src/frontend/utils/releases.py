"""Backend release client and Qt update workers."""

import html
import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError
from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot

from src.config import (
    BACKEND_URL,
    RELEASE_CHECK_TIMEOUT_SECONDS,
    RELEASE_STAGE_TIMEOUT_SECONDS,
)
from src.contracts.releases import (
    ReleaseEntry,
    ReleaseStageResponse,
    ReleaseUpdateResponse,
)
from src.utils.logging import logger

# --------------------------------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------------------------------
LATEST_RELEASE_URL = f"{BACKEND_URL}/api/v1/releases/latest"
STAGE_LATEST_RELEASE_URL = f"{BACKEND_URL}/api/v1/releases/latest/stage"

# --------------------------------------------------------------------------------------------------
# Requests
# --------------------------------------------------------------------------------------------------
def get_latest_release_update() -> ReleaseUpdateResponse:
    """Request and validate the latest release information from the backend."""
    try:
        with urlopen(LATEST_RELEASE_URL, timeout=RELEASE_CHECK_TIMEOUT_SECONDS) as response:
            return ReleaseUpdateResponse.model_validate_json(response.read())
    except HTTPError as exc:
        raise RuntimeError(_get_http_error_detail(exc, "Could not check for updates.")) from exc
    except (URLError, TimeoutError, OSError, ValidationError) as exc:
        raise RuntimeError("Could not check for updates through the backend.") from exc
# --------------------------------------------------------------------------------------------------
def stage_latest_release_update() -> ReleaseStageResponse:
    """Ask the backend to prepare the latest application release for installation."""
    request = Request(
        STAGE_LATEST_RELEASE_URL,
        method="POST",
    )
    try:
        with urlopen(request, timeout=RELEASE_STAGE_TIMEOUT_SECONDS) as response:
            return ReleaseStageResponse.model_validate_json(response.read())
    except HTTPError as exc:
        raise RuntimeError(_get_http_error_detail(exc, "Could not prepare the update.")) from exc
    except (URLError, TimeoutError, OSError, ValidationError) as exc:
        raise RuntimeError("Could not prepare the update through the backend.") from exc

# --------------------------------------------------------------------------------------------------
# Update check worker
# --------------------------------------------------------------------------------------------------
class _ReleaseUpdateWorker(QObject):
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
class ReleaseUpdateChecker(QObject):
    """Manage asynchronous release checks and their worker-thread lifecycle."""

    succeeded = Signal(ReleaseUpdateResponse)
    failed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _ReleaseUpdateWorker | None = None

    @property
    def is_running(self) -> bool:
        """Return whether a release check is currently running."""
        return self._thread is not None

    def start(self) -> bool:
        """Start a release check and return whether it was started."""
        if self.is_running:
            return False
        thread = QThread(self)
        worker = _ReleaseUpdateWorker()
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

# --------------------------------------------------------------------------------------------------
# Update staging worker
# --------------------------------------------------------------------------------------------------
class _ReleaseStageWorker(QObject):
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
class ReleaseUpdateStager(QObject):
    """Manage asynchronous update staging and its worker-thread lifecycle."""

    succeeded = Signal(ReleaseStageResponse)
    failed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _ReleaseStageWorker | None = None

    @property
    def is_running(self) -> bool:
        """Return whether update preparation is currently running."""
        return self._thread is not None

    def start(self) -> bool:
        """Start update preparation and return whether it was started."""
        if self.is_running:
            return False
        thread = QThread(self)
        worker = _ReleaseStageWorker()
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

# --------------------------------------------------------------------------------------------------
# Presentation
# --------------------------------------------------------------------------------------------------
def format_release_entries_html(releases: list[ReleaseEntry]) -> str:
    """Format release entries as a small HTML document."""
    if not releases:
        return "<!doctype html><html><body><p>No release notes available.</p></body></html>"
    parts = ["<!doctype html>", "<html>", "<body>"]
    for release in reversed(releases):
        version = html.escape(release.version)
        created_at_local = html.escape(_format_release_datetime_local(release.created_at_utc))
        parts.append(f"<h2>Version {version}</h2>")
        parts.append(f"<p><code>{created_at_local}</code></p>")
        if release.changes:
            parts.append("<ul>")
            parts.extend(f"<li>{html.escape(change)}</li>" for change in release.changes)
            parts.append("</ul>")
        else:
            parts.append("<p>No changes listed.</p>")
    parts.extend(["</body>", "</html>"])
    return "\n".join(parts)

# --------------------------------------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------------------------------------
def _format_release_datetime_local(value: datetime) -> str:
    return value.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
# --------------------------------------------------------------------------------------------------
def _get_http_error_detail(error: HTTPError, fallback_message: str) -> str:
    try:
        body = json.loads(error.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return fallback_message
    detail = body.get("detail") if isinstance(body, dict) else None
    return detail if isinstance(detail, str) else fallback_message
