"""Uvicorn backend server runner."""

import uvicorn

from src.backend.application import application
from src.backend.utils.tmp import clean_tmp_dir
from src.config import APP_NAME, BACKEND_HOST, BACKEND_PORT
from src.utils.logging import init_logging, logger

# --------------------------------------------------------------------------------------------------
# Server lifecycle
# --------------------------------------------------------------------------------------------------
def run_backend() -> int:
    """Run the backend server in the current process."""
    init_logging("backend")
    clean_tmp_dir()
    logger.info(f"Starting {APP_NAME} backend...")
    config = uvicorn.Config(
        application,
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        log_config=None,
        log_level="info",
    )
    server = uvicorn.Server(config)
    try:
        server.run()
    except KeyboardInterrupt:
        return 130
    finally:
        logger.info(f"Closing {APP_NAME} backend...")
    return 0 if server.started else 1
