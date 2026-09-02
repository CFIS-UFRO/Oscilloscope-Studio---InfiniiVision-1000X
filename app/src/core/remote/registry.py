"""Registry of the functions an external client is allowed to invoke."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

# --------------------------------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------------------------------
class RemoteError(Exception):
    """Base class for remote-control dispatch failures."""
# --------------------------------------------------------------------------------------------------
class UnknownCommandError(RemoteError):
    """Raised when a request names a command that is not registered."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Unknown command: {name}")
        self.name = name
# --------------------------------------------------------------------------------------------------
class CommandParamsError(RemoteError):
    """Raised when a request carries parameters that fail validation."""

    def __init__(self, name: str, reason: str) -> None:
        super().__init__(f"Invalid parameters for command '{name}': {reason}")
        self.name = name
        self.reason = reason

# --------------------------------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class RemoteCommand:
    """One remotely invocable function and its optional parameter model."""

    name: str
    handler: Callable[..., Any]
    params_model: type[BaseModel] | None = None
    description: str = ""
# --------------------------------------------------------------------------------------------------
class RemoteRegistry:
    """Hold the set of remotely invocable commands and dispatch requests to them."""

    def __init__(self) -> None:
        self._commands: dict[str, RemoteCommand] = {}

    def register(
        self,
        name: str,
        handler: Callable[..., Any],
        *,
        params_model: type[BaseModel] | None = None,
        description: str = "",
    ) -> None:
        """Expose a function under a command name, rejecting duplicate names."""
        if name in self._commands:
            raise ValueError(f"Command already registered: {name}")
        # Copy-on-write: the server thread reads this dict while the GUI registers into it
        self._commands = {
            **self._commands,
            name: RemoteCommand(name, handler, params_model, description),
        }

    def names(self) -> frozenset[str]:
        """Return an immutable snapshot of the registered command names."""
        return frozenset(self._commands)

    def dispatch(self, name: str, raw_params: dict[str, Any]) -> Any:
        """Validate parameters and run the command handler, returning its result."""
        # Command lookup
        command = self._commands.get(name)
        if command is None:
            raise UnknownCommandError(name)
        # Parameterless command
        if command.params_model is None:
            return command.handler()
        # Validated command
        try:
            params = command.params_model.model_validate(raw_params)
        except ValidationError as exc:
            raise CommandParamsError(name, str(exc)) from exc
        return command.handler(params)
