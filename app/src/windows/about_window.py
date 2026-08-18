"""Application about window."""

import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.config import APP_NAME
from src.utils.about import get_about_info
from src.utils.colors import is_dark_mode
from src.utils.logging import logger
from src.utils.paths import get_logo_file_path
from src.widgets.close_button_widget import CloseButtonWidget

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
                f"{about_info['main_developer']['name']} "
                f"({about_info['main_developer']['email']})",
                word_wrap=False,
            ),
        )
        # Add the laboratory information
        information_layout.addRow(
            "Laboratory",
            self._create_value_label(about_info["laboratory"]["name"], word_wrap=False),
        )
        # Add the university information
        information_layout.addRow(
            "University",
            self._create_value_label(about_info["university"]["name"], word_wrap=False),
        )
        # Attach the information grid
        layout.addLayout(information_layout)
        # Create the centered logo row
        logos_layout = QHBoxLayout()
        logos_layout.setSpacing(24)
        logos_layout.addStretch(1)
        # Add each available institution logo
        for institution in (about_info["laboratory"], about_info["university"]):
            logo_label = self._create_logo_label(institution["logo"])
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

    def _create_logo_label(self, logo_file_name: str) -> QLabel | None:
        # Resolve the logo variant for the active color theme
        logo_file_path = get_logo_file_path(logo_file_name, is_dark_mode())
        # Load the logo image
        pixmap = QPixmap(str(logo_file_path))
        # Skip an unavailable or invalid image
        if pixmap.isNull():
            logger.warning(f"Could not load about logo: {logo_file_path}")
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
