"""Application help window."""

import sys

from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget

from src.utils.logging import logger
from src.frontend.widgets.common.close_button_widget import CloseButtonWidget
from src.frontend.widgets.help.manual_browser import ManualBrowser

# --------------------------------------------------------------------------------------------------
# Dialog
# --------------------------------------------------------------------------------------------------
class HelpWindow(QDialog):
    """Display the indexed application help manuals."""

    def __init__(
        self,
        initial_manual_id: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.resize(800, 500)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        self._manual_browser = ManualBrowser(initial_manual_id, self)
        layout.addWidget(self._manual_browser, 1)
        layout.addWidget(CloseButtonWidget(self))

    def open_manual(self, manual_id: str) -> None:
        """Open a help manual by identifier."""
        self._manual_browser.open_manual(manual_id)

    def show_window(self) -> None:
        """Show, raise, and activate the help window."""
        logger.info(
            f"Opening help window with entry: {self._manual_browser.get_current_manual_log_entry()}"
        )
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        if sys.platform != "darwin":
            self.activateWindow()
