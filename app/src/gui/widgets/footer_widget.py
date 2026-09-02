"""Application footer with release information."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

# --------------------------------------------------------------------------------------------------
# Widget
# --------------------------------------------------------------------------------------------------
class FooterWidget(QWidget):
    """Display application information at the bottom of the main window."""

    def __init__(self, version: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # Root layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        # Version label
        version_label = QLabel(f"Version {version}", self)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(version_label)
