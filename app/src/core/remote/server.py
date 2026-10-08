"""ZeroMQ server exposing registered functions to external clients."""

from collections.abc import Callable
from typing import Any

import zmq
from pydantic import ValidationError, validate_call

from src.core.config import REMOTE_CONTROL_ENDPOINT
from src.core.logging import logger
from src.core.remote.protocol import RemoteRequest, RemoteResponse

# --------------------------------------------------------------------------------------------------
# Server
# --------------------------------------------------------------------------------------------------
class RemoteControlServer:
    """Answer remote requests on a REP socket whenever the consumer asks it to.

    The server owns no thread: libzmq's I/O thread accepts connections and queues incoming
    requests, and ``process_pending`` answers them on the caller's thread without blocking.
    """

    def __init__(self, endpoint: str = REMOTE_CONTROL_ENDPOINT) -> None:
        self._endpoint = endpoint
        self._commands: dict[str, Callable[..., Any]] = {}
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REP)
        self._socket.setsockopt(zmq.LINGER, 0)
        self._is_open = False

    def register(self, name: str, handler: Callable[..., Any]) -> None:
        """Expose a function under a command name; its type hints validate the parameters."""
        if name in self._commands:
            raise ValueError(f"Command already registered: {name}")
        self._commands[name] = validate_call(handler)

    def open(self) -> None:
        """Bind the socket so clients may connect; requests queue until processed."""
        try:
            self._socket.bind(self._endpoint)
        except zmq.ZMQError as exc:
            logger.error(f"Remote control disabled, could not bind {self._endpoint}: {exc}")
            return
        self._is_open = True
        logger.info(f"Remote control listening on {self._endpoint}")

    def close(self) -> None:
        """Close the socket and release the ZeroMQ context."""
        self._is_open = False
        self._socket.close()
        self._context.term()

    def process_pending(self) -> None:
        """Answer every queued request; call it periodically from the consumer's thread."""
        if not self._is_open:
            return
        while True:
            try:
                raw = self._socket.recv(zmq.NOBLOCK)
            except zmq.Again:
                return
            # REP requires exactly one reply per request, so _handle never raises
            self._socket.send_string(self._handle(raw))

    def _handle(self, raw: bytes) -> str:
        # Request parsing
        try:
            request = RemoteRequest.model_validate_json(raw)
        except ValidationError as exc:
            return self._failure(f"Malformed request: {exc}")
        # Command lookup
        handler = self._commands.get(request.command)
        if handler is None:
            return self._failure(f"Unknown command: {request.command}")
        # Execution
        try:
            return RemoteResponse(ok=True, result=handler(**request.params)).model_dump_json()
        except ValidationError as exc:
            return self._failure(f"Invalid parameters for '{request.command}': {exc}")
        except Exception as exc:
            logger.exception(f"Remote command failed: {request.command}")
            return RemoteResponse(ok=False, error=str(exc)).model_dump_json()

    def _failure(self, error: str) -> str:
        logger.warning(f"Rejected remote request: {error}")
        return RemoteResponse(ok=False, error=error).model_dump_json()
