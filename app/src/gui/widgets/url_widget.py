"""Reusable label with icon-based open/copy actions for a URL."""

from typing import cast

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QWidget

from src.gui.utils.colors import is_dark_mode
from src.gui.utils.icon_button import create_icon_button
from src.gui.utils.resources import get_external_link_icon_file_path
from src.gui.widgets.copy_text_widget import CopyTextWidget

# --------------------------------------------------------------------------------------------------
# Widget
# --------------------------------------------------------------------------------------------------
class UrlWidget(CopyTextWidget):
    """Display descriptive text for a URL alongside icon-based open and copy actions."""

    def __init__(self, text: str, url: str, parent: QWidget | None = None) -> None:
        super().__init__(text, url, parent, tooltip="Copy link")
        open_button = create_icon_button(
            get_external_link_icon_file_path(is_dark_mode()), "Open link", self
        )
        open_button.clicked.connect(self._open_url)
        layout = cast(QHBoxLayout, self.layout())
        layout.insertWidget(layout.count() - 1, open_button)

    def _open_url(self) -> None:
        QDesktopServices.openUrl(QUrl(self._value))
