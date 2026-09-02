"""Qt application bootstrap and GUI startup sequence."""

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication

from src.core.config import APP_NAME, ORGANIZATION_NAME, RESTART_EXIT_CODE
from src.core.logging import logger
from src.core.paths import PYPROJECT_FILE_PATH
from src.core.releases import get_pyproject_version
from src.core.remote import RemoteControl
from src.gui.remote.controller import RemoteControlController
from src.gui.utils.resources import ICON_FILE_PATH
from src.gui.windows.main_window import MainWindow

# --------------------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------------------
def run_gui(remote_control: RemoteControl) -> int:
    """Create the Qt application, wire the main window and its services, and run the event loop."""
    # Qt application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setWindowIcon(QIcon(str(ICON_FILE_PATH)))
    app.aboutToQuit.connect(_about_to_quit)
    # Application version
    version = get_pyproject_version(PYPROJECT_FILE_PATH)
    # Main window
    window = MainWindow(
        version=version,
        restart_callback=lambda: _restart(app),
        quit_callback=lambda: _quit(app),
    )
    # Application shortcuts
    _configure_shortcuts(app, window)
    # Remote control
    _configure_remote_control(remote_control, window)
    # Startup tasks
    window.showMaximized()
    QTimer.singleShot(0, window.check_for_updates_on_startup)
    # Event loop
    return app.exec()

# --------------------------------------------------------------------------------------------------
# Shortcuts
# --------------------------------------------------------------------------------------------------
def _configure_shortcuts(app: QApplication, window: MainWindow) -> None:
    """Install the application-wide restart and quit keyboard shortcuts."""
    bindings = (
        (("Ctrl+R", "Meta+R"), lambda: _restart(app)),
        (("Ctrl+Q", "Meta+Q"), lambda: _quit(app)),
    )
    for sequences, handler in bindings:
        for sequence in sequences:
            shortcut = QShortcut(QKeySequence(sequence), window)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(handler)

# --------------------------------------------------------------------------------------------------
# Remote control
# --------------------------------------------------------------------------------------------------
def _configure_remote_control(remote_control: RemoteControl, window: MainWindow) -> None:
    """Bridge the core remote-control channel to the GUI and register its commands."""
    # GUI-side driver (kept alive by its Qt parent)
    RemoteControlController(remote_control, parent=window)
    # Command registrations
    # Register remote commands here, e.g.:
    # remote_control.register("some.command", lambda: ..., description="...")

# --------------------------------------------------------------------------------------------------
# Lifecycle
# --------------------------------------------------------------------------------------------------
def _restart(app: QApplication) -> None:
    """Request a launcher-level application restart."""
    logger.info("Restart requested")
    app.exit(RESTART_EXIT_CODE)
# --------------------------------------------------------------------------------------------------
def _quit(app: QApplication) -> None:
    """Quit the current application process."""
    logger.info("Quit requested")
    app.quit()
# --------------------------------------------------------------------------------------------------
def _about_to_quit() -> None:
    """Record application shutdown."""
    logger.info(f"Closing {APP_NAME}...")
