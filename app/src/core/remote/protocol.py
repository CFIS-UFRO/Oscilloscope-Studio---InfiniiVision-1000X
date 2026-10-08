"""Wire protocol for the remote-control channel, parsed and serialized as JSON."""

from typing import Any

from pydantic import BaseModel

# --------------------------------------------------------------------------------------------------
# Messages
# --------------------------------------------------------------------------------------------------
class RemoteRequest(BaseModel):
    """A command invocation sent by an external client."""

    command: str
    params: dict[str, Any] = {}
# --------------------------------------------------------------------------------------------------
class RemoteResponse(BaseModel):
    """The reply to a request: the command's return value or the reason it failed."""

    ok: bool
    result: Any = None
    error: str | None = None
