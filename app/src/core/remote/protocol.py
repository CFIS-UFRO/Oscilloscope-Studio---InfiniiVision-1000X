"""Wire protocol for the remote-control channel, parsed and serialized as JSON."""

import time
from typing import Any, Literal

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------------------------------
# Messages
# --------------------------------------------------------------------------------------------------
class RemoteRequest(BaseModel):
    """A command invocation sent by an external client on the command socket."""

    id: str | None = None
    command: str
    params: dict[str, Any] = {}
# --------------------------------------------------------------------------------------------------
class RemoteAck(BaseModel):
    """Immediate reply telling the client whether the command was admitted."""

    id: str | None = None
    status: Literal["accepted", "rejected"]
    error: str | None = None
# --------------------------------------------------------------------------------------------------
class RemoteEvent(BaseModel):
    """A message published on the event socket: a command outcome or a domain event."""

    id: str | None = None
    type: str
    command: str | None = None
    payload: dict[str, Any] = {}
    ts: float = Field(default_factory=time.time)
