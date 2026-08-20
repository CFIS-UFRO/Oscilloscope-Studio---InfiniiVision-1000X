"""Application-wide metadata and release configuration."""

# --------------------------------------------------------------------------------------------------
# Application metadata
# --------------------------------------------------------------------------------------------------
APP_NAME = "Oscilloscope Studio"
APP_SLUG = "oscilloscope_studio"
APP_DESCRIPTION = "GUI for controlling Keysight InfiniiVision 1000 X-Series oscilloscopes"
ORGANIZATION_NAME = "CFIS-UFRO"
RESTART_EXIT_CODE = 42

# --------------------------------------------------------------------------------------------------
# Process supervision
# --------------------------------------------------------------------------------------------------
PROCESS_SHUTDOWN_TIMEOUT_SECONDS = 5.0

# --------------------------------------------------------------------------------------------------
# Backend service
# --------------------------------------------------------------------------------------------------
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 57341
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
BACKEND_STARTUP_TIMEOUT_SECONDS = 15.0

# --------------------------------------------------------------------------------------------------
# Release configuration
# --------------------------------------------------------------------------------------------------
RELEASE_REPOSITORY_NAME = "CFIS-UFRO/Oscilloscope-Studio---InfiniiVision-1000X"
RELEASE_REPOSITORY_URL = f"https://github.com/{RELEASE_REPOSITORY_NAME}"
RELEASE_ARCHIVE_PREFIX = APP_SLUG
RELEASE_HTTP_USER_AGENT = "Oscilloscope-Studio-Updater"
