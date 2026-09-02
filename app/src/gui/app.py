"""Qt application bootstrap and lifecycle wiring."""

import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.core.config import APP_NAME, ORGANIZATION_NAME, RESTART_EXIT_CODE
from src.core.logging import logger
from src.gui.utils.resources import ICON_FILE_PATH
from src.gui.windows.main_window import MainWindow

# --------------------------------------------------------------------------------------------------
# Application lifecycle
# --------------------------------------------------------------------------------------------------
def _restart_app(app: QApplication) -> None:
    """Request a launcher-level application restart."""
    logger.info("Restart requested")
    app.exit(RESTART_EXIT_CODE)
# --------------------------------------------------------------------------------------------------
def _quit_app(app: QApplication) -> None:
    """Quit the current application process."""
    logger.info("Quit requested")
    app.quit()
# --------------------------------------------------------------------------------------------------
def _about_to_quit() -> None:
    """Record application shutdown."""
    logger.info(f"Closing {APP_NAME}...")

# --------------------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------------------
def run_gui() -> int:
    """Create the Qt application, show the main window, and run the event loop."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setWindowIcon(QIcon(str(ICON_FILE_PATH)))
    window = MainWindow(
        restart_callback=lambda: _restart_app(app),
        quit_callback=lambda: _quit_app(app),
    )
    app.aboutToQuit.connect(_about_to_quit)
    window.showMaximized()
    QTimer.singleShot(0, window.check_for_updates_on_startup)
    return app.exec()
