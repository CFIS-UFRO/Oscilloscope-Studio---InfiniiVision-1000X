from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

# --------------------------------------------------------------------------------------------------
# Badge colors
# --------------------------------------------------------------------------------------------------
BADGE_COLORS = {
    "gray": "#6f7378",
    "green": "#1f8f4d",
    "orange": "#c46a1a",
    "red": "#b43a35",
}


# --------------------------------------------------------------------------------------------------
def is_dark_mode() -> bool:
    """Returns whether the application uses a dark color scheme."""
    return QApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
