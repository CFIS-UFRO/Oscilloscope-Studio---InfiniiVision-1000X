"""Main frontend window and top-level actions."""

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

from src.config import APP_NAME
from src.frontend.utils.general import get_application_info
from src.frontend.widgets.footer_widget import FooterWidget
from src.frontend.widgets.header_widget import HeaderWidget
from src.frontend.widgets.terminal_widget import TerminalWidget
from src.frontend.windows.about_window import AboutWindow
from src.frontend.windows.help_window import HelpWindow
from src.frontend.windows.release_update_window import ReleaseUpdateWindow
from src.utils.logging import logger

# --------------------------------------------------------------------------------------------------
# Main window
# --------------------------------------------------------------------------------------------------
class MainWindow(QMainWindow):
    """Main application window and reusable application shell."""

    def __init__(
        self,
        restart_callback: Callable[[], None] | None = None,
        apply_update_callback: Callable[[], None] | None = None,
        quit_callback: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        # Application callbacks
        self._restart_callback = restart_callback
        self._apply_update_callback = apply_update_callback
        self._quit_callback = quit_callback
        # Auxiliary windows
        self._about_window: AboutWindow | None = None
        self._help_window: HelpWindow | None = None
        self._release_update_window: ReleaseUpdateWindow | None = None
        # Runtime state
        self._shortcuts: list[QShortcut] = []
        self._closing_from_action = False
        self._version = get_application_info().version
        # Window configuration
        self.setWindowTitle(APP_NAME)
        self.resize(1_200, 720)
        # Interface setup
        self._build_content()
        self._connect_signals()
        self._configure_shortcuts()
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
                apply_update_callback=self._apply_update_callback,
                parent=self,
            )
        return self._release_update_window
