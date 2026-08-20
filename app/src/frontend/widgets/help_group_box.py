"""Section container with a contextual help header."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.frontend.widgets.help_button import HelpButton

# --------------------------------------------------------------------------------------------------
# Widget
# --------------------------------------------------------------------------------------------------
class HelpGroupBox(QWidget):
    """Display a title and help button above a content widget."""

    def __init__(
        self,
        title: str,
        manual_id: str,
        parent: QWidget | None = None,
        with_container: bool = True,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 0, 8, 0)
        header_layout.setSpacing(6)
        title_label = QLabel(title, self)
        title_label.setStyleSheet("font-size: 12px; font-weight: 600;")
        header_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(
            HelpButton(manual_id, self),
            alignment=Qt.AlignmentFlag.AlignVCenter,
        )
        header_layout.addStretch(1)
        layout.addLayout(header_layout)
        content_widget_type = QGroupBox if with_container else QWidget
        self._content_widget = content_widget_type(self)
        layout.addWidget(self._content_widget)

    @property
    def content_widget(self) -> QWidget:
        """Return the widget that owns the section content."""
        return self._content_widget
