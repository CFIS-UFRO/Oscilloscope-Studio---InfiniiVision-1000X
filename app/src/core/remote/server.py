"""Background ZeroMQ server exposing registered commands to external clients."""

import queue
import threading

import zmq
from pydantic import ValidationError

from src.core.config import (
    REMOTE_CONTROL_COMMAND_ENDPOINT,
    REMOTE_CONTROL_EVENT_ENDPOINT,
)
from src.core.logging import logger
from src.core.remote.protocol import RemoteAck, RemoteEvent, RemoteRequest
from src.core.remote.registry import RemoteRegistry

# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------
POLL_INTERVAL_MS = 50
SHUTDOWN_JOIN_TIMEOUT_S = 5.0

# --------------------------------------------------------------------------------------------------
# Server
# --------------------------------------------------------------------------------------------------
class RemoteControlServer:
    """Run a REP command socket and a PUB event socket on a private daemon thread.

    Admitted requests are queued for the consumer to pull with ``poll_command`` and run on
    its own thread; outcomes flow back through ``publish``.
    """

    def __init__(self, registry: RemoteRegistry) -> None:
        self._command_endpoint = REMOTE_CONTROL_COMMAND_ENDPOINT
        self._event_endpoint = REMOTE_CONTROL_EVENT_ENDPOINT
        self._registry = registry
        self._incoming: queue.Queue[RemoteRequest] = queue.Queue()
        self._outgoing: queue.Queue[RemoteEvent] = queue.Queue()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        """Return whether the server thread is currently alive."""
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Start the server thread; a no-op if it is already running."""
        if self.is_running:
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="remote-control-server",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Signal the server thread to shut down and wait for it to finish."""
        if self._thread is None:
            return
        self._stop.set()
        self._thread.join(timeout=SHUTDOWN_JOIN_TIMEOUT_S)
        self._thread = None

    def poll_command(self) -> RemoteRequest | None:
        """Return the next queued request, or ``None``; safe to call from any thread."""
        try:
            return self._incoming.get_nowait()
        except queue.Empty:
            return None

    def publish(self, event: RemoteEvent) -> None:
        """Queue an event for the PUB socket; safe to call from any thread."""
        self._outgoing.put(event)

    # Thread body
    def _run(self) -> None:
        # Socket setup
        context = zmq.Context()
        command_socket = context.socket(zmq.REP)
        event_socket = context.socket(zmq.PUB)
        command_socket.setsockopt(zmq.LINGER, 0)
        event_socket.setsockopt(zmq.LINGER, 0)
        try:
            command_socket.bind(self._command_endpoint)
            event_socket.bind(self._event_endpoint)
        except zmq.ZMQError as exc:
            logger.error(f"Remote control disabled, could not bind sockets: {exc}")
            command_socket.close()
            event_socket.close()
            context.term()
            return
        logger.info(
            f"Remote control listening for commands on {self._command_endpoint} "
            f"and events on {self._event_endpoint}"
        )
        # Poll loop
        poller = zmq.Poller()
        poller.register(command_socket, zmq.POLLIN)
        try:
            while not self._stop.is_set():
                ready = dict(poller.poll(timeout=POLL_INTERVAL_MS))
                if ready.get(command_socket) == zmq.POLLIN:
                    self._handle_request(command_socket)
                self._drain_outgoing(event_socket)
        finally:
            poller.unregister(command_socket)
            command_socket.close()
            event_socket.close()
            context.term()
            logger.info("Remote control stopped")

    def _handle_request(self, command_socket: zmq.Socket) -> None:
        # Inbound message
        try:
            raw = command_socket.recv_string()
        except (zmq.ZMQError, UnicodeDecodeError):
            logger.exception("Failed to receive remote command")
            return
        # Acknowledgement (REP requires exactly one reply per request)
        ack, request = self._build_ack(raw)
        try:
            command_socket.send_string(ack.model_dump_json())
        except zmq.ZMQError:
            logger.exception("Failed to acknowledge remote command")
            return
        # Hand-off of an admitted command to the consumer
        if request is not None:
            self._incoming.put(request)

    def _build_ack(self, raw: str) -> tuple[RemoteAck, RemoteRequest | None]:
        # Message parsing
        try:
            request = RemoteRequest.model_validate_json(raw)
        except ValidationError as exc:
            return RemoteAck(status="rejected", error=f"Malformed request: {exc}"), None
        # Exposure check
        if request.command not in self._registry.names():
            return (
                RemoteAck(
                    id=request.id,
                    status="rejected",
                    error=f"Unknown or unexposed command: {request.command}",
                ),
                None,
            )
        return RemoteAck(id=request.id, status="accepted"), request

    def _drain_outgoing(self, event_socket: zmq.Socket) -> None:
        while True:
            try:
                event = self._outgoing.get_nowait()
            except queue.Empty:
                return
            try:
                event_socket.send_string(event.model_dump_json())
            except zmq.ZMQError:
                logger.exception("Failed to publish remote event")
