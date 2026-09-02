"""Qt application bootstrap and GUI startup sequence."""

import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from pydantic import BaseModel

from src.core.config import APP_NAME, ORGANIZATION_NAME, RESTART_EXIT_CODE
from src.core.logging import logger
from src.core.paths import PYPROJECT_FILE_PATH
from src.core.releases import get_pyproject_version
from src.core.remote import RemoteControl
from src.gui.remote.controller import RemoteControlController
from src.gui.utils.resources import ICON_FILE_PATH
from src.gui.windows.main_window import MainWindow

# --------------------------------------------------------------------------------------------------
# Remote command parameters
# --------------------------------------------------------------------------------------------------
class TerminalAppendParams(BaseModel):
    """Parameters for the ``terminal.append`` remote command."""

    text: str
    level: str = "INFO"

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
    # Remote control
    _configure_remote_control(remote_control, window, version)
    # Startup tasks
    window.showMaximized()
    QTimer.singleShot(0, window.check_for_updates_on_startup)
    # Event loop
    return app.exec()

# --------------------------------------------------------------------------------------------------
# Remote control
# --------------------------------------------------------------------------------------------------
def _configure_remote_control(
    remote_control: RemoteControl, window: MainWindow, version: str
) -> None:
    """Bridge the core remote-control channel to the GUI and register its commands."""
    # GUI-side driver (kept alive by its Qt parent)
    RemoteControlController(remote_control, parent=window)
    # Terminal output
    remote_control.register(
        "terminal.append",
        lambda params: window.append_terminal_message(params.level, params.text),
        params_model=TerminalAppendParams,
        description="Append a line to the in-app terminal panel.",
    )
    # Application version
    remote_control.register(
        "app.version",
        lambda: version,
        description="Return the running application version.",
    )

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
