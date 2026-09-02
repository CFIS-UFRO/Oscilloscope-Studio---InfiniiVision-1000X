"""The application's remote-control extension: a command registry plus a ZeroMQ server."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from src.core.remote.protocol import RemoteEvent, RemoteRequest
from src.core.remote.registry import RemoteRegistry
from src.core.remote.server import RemoteControlServer

# --------------------------------------------------------------------------------------------------
# Facade
# --------------------------------------------------------------------------------------------------
class RemoteControl:
    """Own the registry and the background server, and mediate between them and a consumer.
    """

    def __init__(self) -> None:
        self._registry = RemoteRegistry()
        self._server = RemoteControlServer(self._registry)

    def register(
        self,
        name: str,
        handler: Callable[..., Any],
        *,
        params_model: type[BaseModel] | None = None,
        description: str = "",
    ) -> None:
        """Expose a function under a command name so external clients may invoke it."""
        self._registry.register(
            name, handler, params_model=params_model, description=description
        )

    def dispatch(self, name: str, params: dict[str, Any]) -> Any:
        """Validate parameters and run the named command, returning its result."""
        return self._registry.dispatch(name, params)

    def start(self) -> None:
        """Start listening for remote commands."""
        self._server.start()

    def stop(self) -> None:
        """Stop the server and wait for its thread to finish."""
        self._server.stop()

    def poll_command(self) -> RemoteRequest | None:
        """Return the next queued request, or ``None`` when none is pending."""
        return self._server.poll_command()

    def publish(self, event: RemoteEvent) -> None:
        """Publish an event on the event socket; safe to call from any thread."""
        self._server.publish(event)
