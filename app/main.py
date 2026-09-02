"""Oscilloscope Studio entry point: start core services, then launch the GUI."""

from src.core.config import APP_NAME
from src.core.logging import init_logging, logger
from src.core.tmp import clean_tmp_dir
from src.gui.app import run_gui

# --------------------------------------------------------------------------------------------------
# Application startup
# --------------------------------------------------------------------------------------------------
def main() -> int:
    """Initialize core services and hand control to the GUI."""
    init_logging()
    clean_tmp_dir()
    logger.info(f"Starting {APP_NAME}...")
    return run_gui()

# --------------------------------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    raise SystemExit(main())
