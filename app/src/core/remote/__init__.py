"""Hardware-agnostic remote-control transport, protocol, and command registry."""

from src.core.remote.control import RemoteControl
from src.core.remote.registry import (
    CommandParamsError,
    RemoteError,
    RemoteRegistry,
    UnknownCommandError,
)

__all__ = [
    "CommandParamsError",
    "RemoteControl",
    "RemoteError",
    "RemoteRegistry",
    "UnknownCommandError",
]
