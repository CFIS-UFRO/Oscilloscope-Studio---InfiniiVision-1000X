"""Reusable badge label widget."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

from src.gui.utils.colors import BADGE_COLORS


# --------------------------------------------------------------------------------------------------
# Widget
# --------------------------------------------------------------------------------------------------
class BadgeWidget(QLabel):
    """Display centered text on a rounded, colored background."""

    def __init__(
        self,
        text: str,
        color: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(24)
        self.set_color(color)

    def set_color(self, color: str) -> None:
        """Set the badge background to a supported named color."""
        if color not in BADGE_COLORS:
            supported_colors = ", ".join(sorted(BADGE_COLORS))
            raise ValueError(
                f"Unsupported badge color '{color}'. Supported colors: {supported_colors}"
            )
        self.setStyleSheet(
            f"""
            background-color: {BADGE_COLORS[color]};
            border-radius: 12px;
            color: white;
            font-size: 12px;
            font-weight: 600;
            padding: 0 12px;
            """
        )
