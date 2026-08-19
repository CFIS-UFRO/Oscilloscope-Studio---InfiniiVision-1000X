"""Main application window and top-level actions."""

from collections.abc import Callable

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QCloseEvent, QCursor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.config import APP_NAME
from src.utils.logging import logger
from src.utils.paths import get_pyproject_file_path
from src.utils.releases import get_pyproject_version
from src.widgets.terminal_widget import TerminalWidget
from src.windows.about_window import AboutWindow
from src.windows.help_window import HelpWindow
from src.windows.release_update_window import ReleaseUpdateWindow

# --------------------------------------------------------------------------------------------------
# Main window
# --------------------------------------------------------------------------------------------------
class MainWindow(QMainWindow):
    """Main application window and reusable application shell."""

    def __init__(
        self,
        restart_callback: Callable[[], None] | None = None,
        quit_callback: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self._restart_callback = restart_callback
        self._quit_callback = quit_callback
        self._about_window: AboutWindow | None = None
        self._help_window: HelpWindow | None = None
        self._release_update_window: ReleaseUpdateWindow | None = None
        self._shortcuts: list[QShortcut] = []
        self._closing_from_action = False
        self._version = get_pyproject_version(get_pyproject_file_path())
        self.setWindowTitle(APP_NAME)
        self.resize(1_200, 720)
        self._build_content()
        self._configure_shortcuts()
        QTimer.singleShot(2000, lambda: logger.info(f"Welcome to {APP_NAME}"))

    def _build_content(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(24, 24, 24, 16)
        layout.setSpacing(16)
        title_label = QLabel(APP_NAME, central_widget)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 26px; font-weight: 600;")
        layout.addWidget(title_label)
        separator = QFrame(central_widget)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        actions_layout = QHBoxLayout()
        actions_layout.addStretch(1)
        updates_button = QPushButton("Check for updates", central_widget)
        updates_button.clicked.connect(self._open_release_update_window)
        actions_layout.addWidget(updates_button)
        help_button = QPushButton("Help", central_widget)
        help_button.clicked.connect(self._open_help_window)
        actions_layout.addWidget(help_button)
        about_button = QPushButton("About", central_widget)
        about_button.clicked.connect(self._open_about_window)
        actions_layout.addWidget(about_button)
        actions_layout.addStretch(1)
        layout.addLayout(actions_layout)
        content_splitter = QSplitter(Qt.Orientation.Vertical, central_widget)
        content_splitter.setChildrenCollapsible(False)
        content_splitter.setHandleWidth(8)
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
        self._terminal_widget = TerminalWidget(content_splitter)
        content_splitter.addWidget(self._terminal_widget)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 0)
        content_splitter.setSizes([1_000, TerminalWidget.INITIAL_HEIGHT])
        layout.addWidget(content_splitter, 1)
        version_label = QLabel(f"Version {self._version}", central_widget)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(version_label)

    def _configure_shortcuts(self) -> None:
        if self._restart_callback is not None:
            for sequence in ("Ctrl+R", "Meta+R"):
                shortcut = QShortcut(QKeySequence(sequence), self)
                shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
                shortcut.activated.connect(self._restart_callback)
                self._shortcuts.append(shortcut)
        for sequence in ("Ctrl+Q", "Meta+Q"):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(self._quit)
            self._shortcuts.append(shortcut)

    def center_on_screen(self) -> None:
        """Center the window on the screen containing the mouse cursor."""
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen is None:
            return
        window_frame = self.frameGeometry()
        window_frame.moveCenter(screen.availableGeometry().center())
        self.move(window_frame.topLeft())

    def check_for_updates_on_startup(self) -> None:
        """Check for a new release without showing current-version or error dialogs."""
        self._get_release_update_window().check_for_updates_on_startup()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Route window-manager closes through the configured quit callback."""
        if self._quit_callback is None or self._closing_from_action:
            event.accept()
            return
        event.ignore()
        self._closing_from_action = True
        self._quit_callback()

    def _quit(self) -> None:
        self._closing_from_action = True
        if self._quit_callback is not None:
            self._quit_callback()
            return
        self.close()

    def _open_help_window(self) -> None:
        if self._help_window is None:
            self._help_window = HelpWindow(initial_manual_id="getting-started", parent=self)
        self._help_window.show_window()

    def _open_about_window(self) -> None:
        if self._about_window is None:
            self._about_window = AboutWindow(parent=self)
        self._about_window.show_window()

    def _open_release_update_window(self) -> None:
        self._get_release_update_window().check_for_updates()

    def _get_release_update_window(self) -> ReleaseUpdateWindow:
        if self._release_update_window is None:
            self._release_update_window = ReleaseUpdateWindow(
                restart_callback=self._restart_callback,
                parent=self,
            )
        return self._release_update_window
