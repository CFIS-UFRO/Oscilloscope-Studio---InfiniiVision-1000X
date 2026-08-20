"""Application header with top-level actions."""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# --------------------------------------------------------------------------------------------------
# Widget
# --------------------------------------------------------------------------------------------------
class HeaderWidget(QWidget):
    """Display the application title, separator, and top-level actions."""

    # Action signals
    check_for_updates_requested = Signal()
    help_requested = Signal()
    about_requested = Signal()

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # Root layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        # Application title
        title_label = QLabel(title, self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 26px; font-weight: 600;")
        layout.addWidget(title_label)
        # Horizontal separator
        separator = QFrame(self)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        # Actions row
        actions_layout = QHBoxLayout()
        actions_layout.addStretch(1)
        # Update action
        updates_button = QPushButton("Check for updates", self)
        updates_button.clicked.connect(self.check_for_updates_requested.emit)
        actions_layout.addWidget(updates_button)
        # Help action
        help_button = QPushButton("Help", self)
        help_button.clicked.connect(self.help_requested.emit)
        actions_layout.addWidget(help_button)
        # About action
        about_button = QPushButton("About", self)
        about_button.clicked.connect(self.about_requested.emit)
        actions_layout.addWidget(about_button)
        actions_layout.addStretch(1)
        layout.addLayout(actions_layout)
