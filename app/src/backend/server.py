"""Uvicorn backend server runner."""

import uvicorn

from src.backend.application import application
from src.config import BACKEND_HOST, BACKEND_PORT

# --------------------------------------------------------------------------------------------------
# Server lifecycle
# --------------------------------------------------------------------------------------------------
def run_backend() -> int:
    """Run the backend server in the current process."""
    config = uvicorn.Config(
        application,
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)
    try:
        server.run()
    except KeyboardInterrupt:
        return 130
    return 0 if server.started else 1
