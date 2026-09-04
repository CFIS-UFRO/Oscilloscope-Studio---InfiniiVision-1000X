"""Reusable label with an icon-based copy action for a fixed piece of text."""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QWidget

from src.gui.utils.colors import is_dark_mode
from src.gui.utils.icon_button import create_icon_button
from src.gui.utils.resources import get_check_icon_file_path, get_copy_icon_file_path

# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------
COPIED_FEEDBACK_DURATION_MS = 1200

# --------------------------------------------------------------------------------------------------
# Widget
# --------------------------------------------------------------------------------------------------
class CopyTextWidget(QWidget):
    """Display descriptive text alongside a value and an icon-based copy action."""

    def __init__(
        self, text: str, value: str, parent: QWidget | None = None, tooltip: str = "Copy"
    ) -> None:
        super().__init__(parent)
        self._value = value
        self._copy_icon = QIcon(str(get_copy_icon_file_path(is_dark_mode())))
        self._check_icon = QIcon(str(get_check_icon_file_path(is_dark_mode())))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        text_label = QLabel(f"{text} {value}", self)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(text_label)
        self._copy_button = create_icon_button(get_copy_icon_file_path(is_dark_mode()), tooltip, self)
        self._copy_button.clicked.connect(self._copy_value)
        layout.addWidget(self._copy_button)
        layout.addStretch(1)

    def _copy_value(self) -> None:
        QApplication.clipboard().setText(self._value)
        self._copy_button.setIcon(self._check_icon)
        QTimer.singleShot(COPIED_FEEDBACK_DURATION_MS, lambda: self._copy_button.setIcon(self._copy_icon))
