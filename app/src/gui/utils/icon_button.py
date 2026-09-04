"""Shared factory for small transparent icon-only buttons."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QSizePolicy, QWidget

# --------------------------------------------------------------------------------------------------
# Factory
# --------------------------------------------------------------------------------------------------
def create_icon_button(icon_file_path: Path, tooltip: str, parent: QWidget) -> QPushButton:
    """Build a fixed-size, borderless button showing the given icon."""
    button = QPushButton(parent)
    button.setFixedSize(20, 20)
    button.setIconSize(QSize(14, 14))
    button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    button.setStyleSheet("QPushButton { background: transparent; border: none; }")
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setIcon(QIcon(str(icon_file_path)))
    button.setToolTip(tooltip)
    return button
