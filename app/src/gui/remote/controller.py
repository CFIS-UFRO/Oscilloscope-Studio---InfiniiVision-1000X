"""GUI-side driver that answers remote requests on the Qt event loop."""

from PySide6.QtCore import QObject, QTimer

from src.core.remote import RemoteControlServer

# --------------------------------------------------------------------------------------------------
# Controller
# --------------------------------------------------------------------------------------------------
class RemoteControlController(QObject):
    """Periodically let the server answer queued requests on the GUI thread.

    Every handler therefore runs on the GUI thread and may touch widgets directly.
    """

    PROCESS_INTERVAL_MS = 25

    def __init__(self, server: RemoteControlServer, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(self.PROCESS_INTERVAL_MS)
        self._timer.timeout.connect(server.process_pending)
        self._timer.start()
