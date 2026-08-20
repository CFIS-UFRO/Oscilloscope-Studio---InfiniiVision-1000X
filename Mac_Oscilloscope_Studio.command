#!/usr/bin/env bash
set -euo pipefail

# ##################################################################################################
# Launch Oscilloscope Studio on macOS with a project-local uv installation and Python environment.
# ##################################################################################################

# --------------------------------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR/app"
UV_DIR="$APP_DIR/.uv"
UV_BIN="$UV_DIR/uv"
UV_CACHE_DIR="$UV_DIR/cache"
UV_PYTHON_INSTALL_DIR="$UV_DIR/python"
UV_PROJECT_ENVIRONMENT="$UV_DIR/venv"
UV_MANAGED_PYTHON=1 # Require uv-managed Python
MAIN_FILE="$APP_DIR/main.py"
RELEASE_MODULE="scripts.create_release"
UPDATE_MODULE="scripts.apply_update"
cd "$APP_DIR"

# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------
RESTART_EXIT_CODE=42
APPLY_UPDATE_EXIT_CODE=43

# --------------------------------------------------------------------------------------------------
# uv installation
# --------------------------------------------------------------------------------------------------
if [ ! -x "$UV_BIN" ]; then
    mkdir -p "$UV_DIR"
    export UV_INSTALL_DIR="$UV_DIR"
    export INSTALLER_NO_MODIFY_PATH=1
    if command -v curl >/dev/null 2>&1; then
        echo "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    else
        echo "curl is required to install uv."
        exit 1
    fi
fi
export UV_CACHE_DIR
export UV_PYTHON_INSTALL_DIR
export UV_PROJECT_ENVIRONMENT
export UV_MANAGED_PYTHON

# --------------------------------------------------------------------------------------------------
# Developer release
# --------------------------------------------------------------------------------------------------
if [ "${1:-}" = "release" ]; then
    "$UV_BIN" run python -m "$RELEASE_MODULE"
    exit $?
fi

# --------------------------------------------------------------------------------------------------
# Application launch and restart
# --------------------------------------------------------------------------------------------------
while true; do
    # Run the supervisor, which starts the backend and frontend processes
    if "$UV_BIN" run python "$MAIN_FILE"; then
        # Record a successful application exit
        exit_code=0
    else
        # Record application errors and launcher control codes
        exit_code=$?
    fi
    # Restart immediately when the application requests a regular restart
    if [ "$exit_code" -eq "$RESTART_EXIT_CODE" ]; then
        echo "Restarting Oscilloscope Studio..."
        continue
    fi
    # Apply a prepared update after the supervisor has stopped both application processes
    if [ "$exit_code" -eq "$APPLY_UPDATE_EXIT_CODE" ]; then
        if "$UV_BIN" run python -m "$UPDATE_MODULE"; then
            # Start the newly updated application
            echo "Restarting Oscilloscope Studio..."
            continue
        else
            # Stop the launcher when the updater fails
            update_exit_code=$?
            exit "$update_exit_code"
        fi
    fi
    # Propagate normal exits and unhandled application errors to the calling terminal
    exit "$exit_code"
done
