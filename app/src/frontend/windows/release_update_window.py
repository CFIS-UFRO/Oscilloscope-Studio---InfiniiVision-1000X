"""Release update dialog and installation action."""

import sys
from collections.abc import Callable

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.config import APP_NAME
from src.contracts.releases import ReleaseStageResponse, ReleaseUpdateResponse
from src.frontend.utils.releases import ReleaseUpdateChecker, ReleaseUpdateStager
from src.frontend.widgets.release_update_details import ReleaseUpdateDetails
from src.utils.logging import logger

# --------------------------------------------------------------------------------------------------
# Dialog
# --------------------------------------------------------------------------------------------------
class ReleaseUpdateWindow(QDialog):
    """Display the latest release and install it when appropriate."""

    def __init__(
        self,
        apply_update_callback: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        # Update state
        self._release_update: ReleaseUpdateResponse | None = None
        self._apply_update_callback = apply_update_callback
        self._silent_check = False
        self._allow_result_window = True
        self._details: ReleaseUpdateDetails | None = None
        # Background release checker
        self._update_checker = ReleaseUpdateChecker(self)
        self._update_checker.succeeded.connect(self._handle_check_success)
        self._update_checker.failed.connect(self._handle_check_failure)
        self._update_stager = ReleaseUpdateStager(self)
        self._update_stager.succeeded.connect(self._handle_stage_success)
        self._update_stager.failed.connect(self._handle_stage_failure)
        # Dialog configuration
        self.setWindowTitle("Updates")
        self.resize(700, 500)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)
        # Release status content
        self._status_label = QLabel("Obtaining release information...", self)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        self._layout.addWidget(self._status_label, 1)
        # Dialog actions
        actions_layout = QHBoxLayout()
        actions_layout.addStretch(1)
        self._update_button = QPushButton("Install update", self)
        self._update_button.setEnabled(False)
        self._update_button.clicked.connect(self._handle_update_clicked)
        actions_layout.addWidget(self._update_button, 0, Qt.AlignmentFlag.AlignCenter)
        self._close_button = QPushButton("Close", self)
        self._close_button.setDefault(True)
        self._close_button.clicked.connect(self.accept)
        actions_layout.addWidget(self._close_button, 0, Qt.AlignmentFlag.AlignCenter)
        actions_layout.addStretch(1)
        self._layout.addLayout(actions_layout)
        # Development-checkout warning
        self._update_disabled_label = QLabel(
            "Git repository detected.\n"
            "In-app updates are disabled.\n"
            "Run 'git pull' from the project directory to download and apply the latest changes.",
            self,
        )
        self._update_disabled_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_disabled_label.setWordWrap(True)
        self._update_disabled_label.setStyleSheet("font-weight: 600;")
        self._update_disabled_label.hide()
        self._layout.addWidget(self._update_disabled_label)

    def check_for_updates(self) -> None:
        """Check for releases and show progress and results."""
        self._start_update_check(silent=False)

    def check_for_updates_on_startup(self) -> None:
        """Check for a new release without showing current-version or error states."""
        self._start_update_check(silent=True)

    def _start_update_check(self, silent: bool) -> None:
        if self._update_checker.is_running:
            if not silent:
                self._silent_check = False
                self._allow_result_window = True
                if self._release_update is not None and self._details is None:
                    self._show_release_details(self._release_update)
                self.show_window()
            return
        self._silent_check = silent
        self._allow_result_window = True
        self._show_status_state("Obtaining release information...")
        if not silent:
            self.show_window()
        self._update_checker.start()

    def show_window(self) -> None:
        """Show, raise, and activate the update dialog."""
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        if sys.platform != "darwin":
            self.activateWindow()

    def done(self, result: int) -> None:
        """Close the dialog without reopening it when an active check completes."""
        if self._update_stager.is_running:
            return
        if self._update_checker.is_running:
            self._allow_result_window = False
        super().done(result)

    @Slot(ReleaseUpdateResponse)
    def _handle_check_success(self, release_update: ReleaseUpdateResponse) -> None:
        self._release_update = release_update
        if not release_update.is_update_available and self._silent_check:
            return
        self._show_release_details(release_update)
        if not self._allow_result_window:
            return
        self.show_window()

    @Slot(str)
    def _handle_check_failure(self, error_message: str) -> None:
        self._show_status_state("Could not obtain release information.")
        if not self._silent_check and self._allow_result_window:
            self.show_window()
            QMessageBox.warning(self, "Updates unavailable", error_message)

    def _show_status_state(self, message: str) -> None:
        self._release_update = None
        if self._details is not None:
            self._details.setParent(None)
            self._details.deleteLater()
            self._details = None
        self._status_label.setText(message)
        self._status_label.show()
        self._update_disabled_label.hide()
        self._update_button.setText("Install update")
        self._update_button.setEnabled(False)
        self._close_button.setDefault(True)

    def _show_release_details(self, release_update: ReleaseUpdateResponse) -> None:
        self._status_label.hide()
        self._details = ReleaseUpdateDetails(release_update, self)
        self._layout.insertWidget(0, self._details, 1)
        self._update_disabled_label.setVisible(release_update.is_git_repository)
        self._update_button.setText("Install update")
        self._update_button.setEnabled(self._can_install_update)
        self._close_button.setDefault(not self._can_install_update)

    @property
    def _can_install_update(self) -> bool:
        return (
            self._release_update is not None
            and self._release_update.is_update_available
            and not self._release_update.is_git_repository
        )

    def _handle_update_clicked(self) -> None:
        if self._release_update is None:
            return
        answer = QMessageBox.question(
            self,
            "Install update",
            f"Install {APP_NAME} {self._release_update.latest_version} and restart the application?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._update_button.setEnabled(False)
        self._update_button.setText("Preparing update...")
        self._close_button.setEnabled(False)
        if not self._update_stager.start():
            return

    @Slot(ReleaseStageResponse)
    def _handle_stage_success(self, staged_update: ReleaseStageResponse) -> None:
        logger.info(f"Requesting installation of release update: {staged_update.version}")
        if self._apply_update_callback is not None:
            self._apply_update_callback()

    @Slot(str)
    def _handle_stage_failure(self, error_message: str) -> None:
        self._update_button.setText("Install update")
        self._update_button.setEnabled(self._can_install_update)
        self._close_button.setEnabled(True)
        QMessageBox.warning(self, "Update failed", error_message)
