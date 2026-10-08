"""GUI-side driver that owns the remote-control server and answers it on the Qt event loop."""

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QCoreApplication, QObject, QTimer, Slot

from src.core.remote import RemoteControlServer

# --------------------------------------------------------------------------------------------------
# Controller
# --------------------------------------------------------------------------------------------------
class RemoteControlController(QObject):
    """Open the remote-control server and periodically let it answer queued requests.

    Every handler therefore runs on the GUI thread and may touch widgets directly.
    """

    PROCESS_INTERVAL_MS = 25

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        # Server
        self._server = RemoteControlServer()
        self._server.open()
        # Request processing
        self._timer = QTimer(self)
        self._timer.setInterval(self.PROCESS_INTERVAL_MS)
        self._timer.timeout.connect(self._server.process_pending)
        self._timer.start()
        # Shutdown
        QCoreApplication.instance().aboutToQuit.connect(self._close)

    def register(self, name: str, handler: Callable[..., Any]) -> None:
        """Expose a function under a command name; its type hints validate the parameters."""
        self._server.register(name, handler)

    @Slot()
    def _close(self) -> None:
        self._timer.stop()
        self._server.close()
