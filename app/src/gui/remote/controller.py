"""GUI-side driver that runs admitted remote commands on the Qt event loop."""

from typing import Any

from PySide6.QtCore import QObject, QTimer, Slot

from src.core.logging import logger
from src.core.remote.control import RemoteControl
from src.core.remote.protocol import RemoteEvent, RemoteRequest
from src.core.remote.registry import RemoteError

# --------------------------------------------------------------------------------------------------
# Controller
# --------------------------------------------------------------------------------------------------
class RemoteControlController(QObject):
    """Drain admitted remote requests on the GUI thread and publish their outcomes.

    A timer polls the server's incoming queue, so no Qt object is ever touched from the
    server thread and no signal is emitted across the thread boundary.
    """

    DRAIN_INTERVAL_MS = 25

    def __init__(self, remote_control: RemoteControl, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._remote_control = remote_control
        self._timer = QTimer(self)
        self._timer.setInterval(self.DRAIN_INTERVAL_MS)
        self._timer.timeout.connect(self._drain)
        self._timer.start()

    def publish(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        *,
        event_id: str | None = None,
        command: str | None = None,
    ) -> None:
        """Publish a domain event or a command outcome on the event socket."""
        self._remote_control.publish(
            RemoteEvent(
                id=event_id,
                type=event_type,
                command=command,
                payload=payload or {},
            )
        )

    @Slot()
    def _drain(self) -> None:
        while True:
            request = self._remote_control.poll_command()
            if request is None:
                return
            self._dispatch(request)

    def _dispatch(self, request: RemoteRequest) -> None:
        try:
            value = self._remote_control.dispatch(request.command, request.params)
        except RemoteError as exc:
            logger.warning(f"Rejected remote command '{request.command}': {exc}")
            self.publish(
                "error", {"message": str(exc)}, event_id=request.id, command=request.command
            )
            return
        except Exception as exc:
            logger.exception(f"Remote command failed: {request.command}")
            self.publish(
                "error", {"message": str(exc)}, event_id=request.id, command=request.command
            )
            return
        self.publish(
            "result", {"value": value}, event_id=request.id, command=request.command
        )
