"""Application about window."""

import sys

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.config import APP_NAME
from src.contracts.api.about import InstitutionInfo
from src.frontend.clients.about import get_about_info, get_about_logo
from src.frontend.utils.colors import is_dark_mode
from src.frontend.utils.paths import get_external_link_icon_file_path
from src.frontend.widgets.common.close_button import CloseButtonWidget
from src.utils.logging import logger

# --------------------------------------------------------------------------------------------------
# Dialog
# --------------------------------------------------------------------------------------------------
class AboutWindow(QDialog):
    """Display application authorship and institutional information."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # Load the application credits
        about_info = get_about_info()
        # Configure the dialog title
        self.setWindowTitle(f"About {APP_NAME}")
        # Create the root layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(16)
        # Add the application title
        title_label = QLabel(APP_NAME, self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(title_label)
        # Create the information grid
        information_layout = QFormLayout()
        information_layout.setHorizontalSpacing(20)
        information_layout.setVerticalSpacing(8)
        # Add the developer information
        information_layout.addRow(
            "Main developer",
            self._create_value_label(
                f"{about_info.main_developer.name} "
                f"({about_info.main_developer.email})",
                word_wrap=False,
            ),
        )
        # Add the laboratory information
        information_layout.addRow(
            "Laboratory",
            self._create_institution_widget(about_info.laboratory),
        )
        # Add the university information
        information_layout.addRow(
            "University",
            self._create_institution_widget(about_info.university),
        )
        # Attach the information grid
        layout.addLayout(information_layout)
        # Create the centered logo row
        logos_layout = QHBoxLayout()
        logos_layout.setSpacing(24)
        logos_layout.addStretch(1)
        # Add each available institution logo
        for institution in (about_info.laboratory, about_info.university):
            logo_path = institution.logos.dark if is_dark_mode() else institution.logos.light
            logo_label = self._create_logo_label(logo_path)
            if logo_label is not None:
                logos_layout.addWidget(logo_label)
        logos_layout.addStretch(1)
        layout.addLayout(logos_layout)
        # Add the dialog action
        layout.addWidget(CloseButtonWidget(self))
        # Fit the dialog to its content
        self.adjustSize()

    def _create_value_label(self, text: str, word_wrap: bool = True) -> QLabel:
        # Create the text label
        label = QLabel(text, self)
        # Apply the requested wrapping behavior
        label.setWordWrap(word_wrap)
        # Allow users to select and copy the text
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return label

    def _create_institution_widget(self, institution: InstitutionInfo) -> QWidget:
        # Create a compact row for the institution name and optional link
        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        # Add the institution name
        layout.addWidget(self._create_value_label(institution.name, word_wrap=False))
        # Add the website action when a URL is configured
        url = institution.url
        if url:
            link_button = QPushButton(widget)
            link_button.setFixedSize(20, 20)
            link_button.setIconSize(QSize(14, 14))
            link_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            link_button.setStyleSheet(
                "QPushButton {"
                " background: transparent;"
                " border: none;"
                "}"
            )
            link_button.setCursor(Qt.CursorShape.PointingHandCursor)
            link_button.setIcon(QIcon(str(get_external_link_icon_file_path(is_dark_mode()))))
            link_button.setToolTip(url)
            link_button.setAccessibleName(f"Open {institution.name} website")
            link_button.clicked.connect(
                lambda _checked=False, target_url=url: QDesktopServices.openUrl(QUrl(target_url))
            )
            # Add a native right-click action for copying the URL
            copy_link_action = QAction("Copy link", link_button)
            copy_link_action.triggered.connect(
                lambda _checked=False, target_url=url: QApplication.clipboard().setText(target_url)
            )
            link_button.addAction(copy_link_action)
            link_button.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
            layout.addWidget(link_button)
        layout.addStretch(1)
        return widget

    def _create_logo_label(self, logo_path: str) -> QLabel | None:
        # Download and load the logo image
        try:
            logo_data = get_about_logo(logo_path)
        except (RuntimeError, ValueError) as exc:
            logger.warning(str(exc))
            return None
        pixmap = QPixmap()
        pixmap.loadFromData(logo_data, "PNG")
        # Skip an unavailable or invalid image
        if pixmap.isNull():
            logger.warning(f"Could not decode About logo: {logo_path}")
            return None
        # Create the fixed logical logo area
        logo_label = QLabel(self)
        logo_size = QSize(64, 48)
        logo_label.setFixedSize(logo_size)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Read the current screen density
        device_pixel_ratio = self.screen().devicePixelRatio()
        # Convert the logical area to physical pixels
        pixel_size = QSize(
            round(logo_size.width() * device_pixel_ratio),
            round(logo_size.height() * device_pixel_ratio),
        )
        # Scale the source at the physical screen resolution
        scaled_pixmap = pixmap.scaled(
            pixel_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        # Preserve the intended logical display size
        scaled_pixmap.setDevicePixelRatio(device_pixel_ratio)
        # Attach the high-density image to the label
        logo_label.setPixmap(scaled_pixmap)
        return logo_label

    def show_window(self) -> None:
        """Show, raise, and activate the about window."""
        # Record the user action
        logger.info("Opening about window")
        # Restore a minimized dialog or show a hidden one
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        # Bring the dialog above the main window
        self.raise_()
        # Request focus explicitly outside macOS
        if sys.platform != "darwin":
            self.activateWindow()
