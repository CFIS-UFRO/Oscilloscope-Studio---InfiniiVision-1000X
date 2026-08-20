"""Qt frontend application lifecycle."""

import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.config import (
    APP_NAME,
    APPLY_UPDATE_EXIT_CODE,
    ORGANIZATION_NAME,
    RESTART_EXIT_CODE,
)
from src.frontend.utils.paths import ICON_FILE_PATH
from src.frontend.windows.main import MainWindow
from src.utils.logging import init_logging, logger

# --------------------------------------------------------------------------------------------------
# Application lifecycle
# --------------------------------------------------------------------------------------------------
def restart_app(app: QApplication) -> None:
    """Request a launcher-level application restart."""
    logger.info("Restart requested")
    app.exit(RESTART_EXIT_CODE)
# --------------------------------------------------------------------------------------------------
def apply_update(app: QApplication) -> None:
    """Request launcher-level installation of a prepared update."""
    logger.info("Update installation requested")
    app.exit(APPLY_UPDATE_EXIT_CODE)
# --------------------------------------------------------------------------------------------------
def quit_app(app: QApplication) -> None:
    """Quit the current frontend process."""
    logger.info("Quit requested")
    app.quit()
# --------------------------------------------------------------------------------------------------
def about_to_quit() -> None:
    """Record frontend shutdown."""
    logger.info(f"Closing {APP_NAME}...")
# --------------------------------------------------------------------------------------------------
def run_frontend() -> int:
    """Initialize and run the Qt frontend in the current process."""
    init_logging("frontend")
    logger.info(f"Starting {APP_NAME} frontend...")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setWindowIcon(QIcon(str(ICON_FILE_PATH)))
    window = MainWindow(
        restart_callback=lambda: restart_app(app),
        apply_update_callback=lambda: apply_update(app),
        quit_callback=lambda: quit_app(app),
    )
    app.aboutToQuit.connect(about_to_quit)
    window.showMaximized()
    QTimer.singleShot(0, window.check_for_updates_on_startup)
    return app.exec()
