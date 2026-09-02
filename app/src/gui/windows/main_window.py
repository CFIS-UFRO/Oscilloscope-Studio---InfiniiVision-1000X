"""Main application window and top-level actions."""

import time
from collections.abc import Callable

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QCloseEvent, QCursor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from pydantic import BaseModel

from src.core.config import APP_NAME
from src.core.logging import logger
from src.core.paths import PYPROJECT_FILE_PATH
from src.core.releases import get_pyproject_version
from src.core.remote import RemoteControl
from src.gui.remote.controller import RemoteControlController
from src.gui.widgets.footer_widget import FooterWidget
from src.gui.widgets.header_widget import HeaderWidget
from src.gui.widgets.terminal_widget import TerminalWidget
from src.gui.windows.about_window import AboutWindow
from src.gui.windows.help_window import HelpWindow
from src.gui.windows.release_update_window import ReleaseUpdateWindow

# --------------------------------------------------------------------------------------------------
# Remote command parameters
# --------------------------------------------------------------------------------------------------
class TerminalAppendParams(BaseModel):
    """Parameters for the ``terminal.append`` remote command."""

    text: str
    level: str = "INFO"

# --------------------------------------------------------------------------------------------------
# Main window
# --------------------------------------------------------------------------------------------------
class MainWindow(QMainWindow):
    """Main application window and reusable application shell."""

    def __init__(
        self,
        remote_control: RemoteControl | None = None,
        restart_callback: Callable[[], None] | None = None,
        quit_callback: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        # Application callbacks
        self._remote_control = remote_control
        self._restart_callback = restart_callback
        self._quit_callback = quit_callback
        # Auxiliary windows
        self._about_window: AboutWindow | None = None
        self._help_window: HelpWindow | None = None
        self._release_update_window: ReleaseUpdateWindow | None = None
        # Runtime state
        self._shortcuts: list[QShortcut] = []
        self._closing_from_action = False
        self._version = get_pyproject_version(PYPROJECT_FILE_PATH)
        # Window configuration
        self.setWindowTitle(APP_NAME)
        self.resize(1_200, 720)
        # Interface setup
        self._build_content()
        self._connect_signals()
        self._configure_shortcuts()
        self._configure_remote_control()
        # Welcome event
        QTimer.singleShot(2000, lambda: logger.info(f"Welcome to {APP_NAME}"))

    def _build_content(self) -> None:
        # Central container
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(12, 12, 12, 4)
        layout.setSpacing(8)
        # Application header
        self._header_widget = HeaderWidget(APP_NAME, central_widget)
        layout.addWidget(self._header_widget)
        # Content splitter
        content_splitter = QSplitter(Qt.Orientation.Vertical, central_widget)
        content_splitter.setChildrenCollapsible(False)
        content_splitter.setHandleWidth(8)
        # Workspace placeholder
        workspace = QWidget(content_splitter)
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        placeholder = QLabel(
            "Oscilloscope controls and acquisition tools will be added here.",
            workspace,
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("font-size: 16px; color: palette(mid);")
        workspace_layout.addWidget(placeholder, 1)
        content_splitter.addWidget(workspace)
        # Terminal panel
        self._terminal_widget = TerminalWidget(content_splitter)
        content_splitter.addWidget(self._terminal_widget)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 0)
        content_splitter.setSizes([1_000, TerminalWidget.INITIAL_HEIGHT])
        layout.addWidget(content_splitter, 1)
        # Application footer
        self._footer_widget = FooterWidget(self._version, central_widget)
        layout.addWidget(self._footer_widget)

    def _connect_signals(self) -> None:
        # Header actions
        self._header_widget.check_for_updates_requested.connect(
            self._open_release_update_window
        )
        self._header_widget.help_requested.connect(self._open_help_window)
        self._header_widget.about_requested.connect(self._open_about_window)

    def _configure_shortcuts(self) -> None:
        # Restart shortcuts
        if self._restart_callback is not None:
            for sequence in ("Ctrl+R", "Meta+R"):
                shortcut = QShortcut(QKeySequence(sequence), self)
                shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
                shortcut.activated.connect(self._restart_callback)
                self._shortcuts.append(shortcut)
        # Quit shortcuts
        for sequence in ("Ctrl+Q", "Meta+Q"):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(self._quit)
            self._shortcuts.append(shortcut)

    def _configure_remote_control(self) -> None:
        if self._remote_control is None:
            return
        self._remote_controller = RemoteControlController(self._remote_control, parent=self)
        self._register_remote_commands()

    def _register_remote_commands(self) -> None:
        # Terminal output
        self._remote_control.register(
            "terminal.append",
            self._remote_append_terminal,
            params_model=TerminalAppendParams,
            description="Append a line to the in-app terminal panel.",
        )
        # Application version
        self._remote_control.register(
            "app.version",
            lambda: self._version,
            description="Return the running application version.",
        )

    def _remote_append_terminal(self, params: TerminalAppendParams) -> None:
        self._terminal_widget.append_message(time.time(), params.level, params.text)

    def center_on_screen(self) -> None:
        """Center the window on the screen containing the mouse cursor."""
        # Target screen
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen is None:
            return
        # Centered position
        window_frame = self.frameGeometry()
        window_frame.moveCenter(screen.availableGeometry().center())
        self.move(window_frame.topLeft())

    def check_for_updates_on_startup(self) -> None:
        """Check for a new release without showing current-version or error dialogs."""
        self._get_release_update_window().check_for_updates_on_startup()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Route window-manager closes through the configured quit callback."""
        # Direct close
        if self._quit_callback is None or self._closing_from_action:
            event.accept()
            return
        # Delegated close
        event.ignore()
        self._closing_from_action = True
        self._quit_callback()

    def _quit(self) -> None:
        # Close state
        self._closing_from_action = True
        if self._quit_callback is not None:
            self._quit_callback()
            return
        self.close()

    def _open_help_window(self) -> None:
        # Lazy initialization
        if self._help_window is None:
            self._help_window = HelpWindow(initial_manual_id="getting-started", parent=self)
        self._help_window.show_window()

    def _open_about_window(self) -> None:
        # Lazy initialization
        if self._about_window is None:
            self._about_window = AboutWindow(parent=self)
        self._about_window.show_window()

    def _open_release_update_window(self) -> None:
        self._get_release_update_window().check_for_updates()

    def _get_release_update_window(self) -> ReleaseUpdateWindow:
        # Lazy initialization
        if self._release_update_window is None:
            self._release_update_window = ReleaseUpdateWindow(
                restart_callback=self._restart_callback,
                parent=self,
            )
        return self._release_update_window
