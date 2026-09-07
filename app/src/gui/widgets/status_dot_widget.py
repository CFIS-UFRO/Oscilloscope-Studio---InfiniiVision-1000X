"""Reusable status dot widget."""

from PySide6.QtWidgets import QLabel, QWidget

from src.gui.widgets.badge_widget import BadgeWidget

# --------------------------------------------------------------------------------------------------
# Widget
# --------------------------------------------------------------------------------------------------
class StatusDotWidget(QLabel):
    """Display a small filled circle whose color follows a named status."""

    DEFAULT_SIZE = 14
    STATUS_COLORS = {
        "idle": "gray",
        "connecting": "gray",
        "connected": "green",
        "disconnecting": "gray",
    }

    def __init__(
        self,
        status: str = "idle",
        size: int = DEFAULT_SIZE,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.set_status(status)

    def set_status(self, status: str) -> None:
        """Set the dot's fill to the color mapped to a supported named status."""
        if status not in self.STATUS_COLORS:
            supported_statuses = ", ".join(sorted(self.STATUS_COLORS))
            raise ValueError(f"Unsupported status '{status}'. Supported statuses: {supported_statuses}")
        color = BadgeWidget.COLORS[self.STATUS_COLORS[status]]
        radius = self._size // 2
        self.setStyleSheet(f"background-color: {color}; border-radius: {radius}px;")
