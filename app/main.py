"""Oscilloscope Studio process supervisor."""

import json
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

from src.config import (
    APP_NAME,
    BACKEND_STARTUP_TIMEOUT_SECONDS,
    BACKEND_URL,
    PROCESS_SHUTDOWN_TIMEOUT_SECONDS,
)
from src.utils.paths import get_app_dir_path

# --------------------------------------------------------------------------------------------------
# Process configuration
# --------------------------------------------------------------------------------------------------
BACKEND_HEALTH_URL = f"{BACKEND_URL}/api/v1/health"

# --------------------------------------------------------------------------------------------------
# Process lifecycle
# --------------------------------------------------------------------------------------------------
def start_process(module_name: str) -> subprocess.Popen[bytes]:
    """Start an application module as an independent child process."""
    # Child process
    return subprocess.Popen(
        [sys.executable, "-m", module_name],
        cwd=get_app_dir_path(),
    )
# --------------------------------------------------------------------------------------------------
def wait_for_first_process_exit(
    processes: tuple[subprocess.Popen[bytes], ...],
) -> int:
    """Return the exit code of the first child process that terminates."""
    while True:
        # Process status
        for process in processes:
            exit_code = process.poll()
            if exit_code is not None:
                return exit_code
        time.sleep(0.25)
# --------------------------------------------------------------------------------------------------
def wait_for_backend(process: subprocess.Popen[bytes]) -> int | None:
    """Wait until the backend is ready or return its early exit code."""
    # Startup window
    deadline = time.monotonic() + BACKEND_STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        # Backend status
        exit_code = process.poll()
        if exit_code is not None:
            return exit_code
        # Health request
        try:
            with urlopen(BACKEND_HEALTH_URL, timeout=0.5) as response:
                health = json.load(response)
        except (OSError, URLError, ValueError):
            time.sleep(0.1)
            continue
        # Ready state
        if health.get("status") == "ready" and process.poll() is None:
            return None
        time.sleep(0.1)
    # Startup timeout
    raise TimeoutError(
        f"Backend did not become ready within {BACKEND_STARTUP_TIMEOUT_SECONDS:g} seconds."
    )
# --------------------------------------------------------------------------------------------------
def stop_process(process: subprocess.Popen[bytes] | None) -> None:
    """Stop a child process and wait for its resources to be released."""
    # Inactive process
    if process is None or process.poll() is not None:
        return
    # Graceful shutdown
    process.terminate()
    try:
        process.wait(timeout=PROCESS_SHUTDOWN_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        # Forced shutdown
        process.kill()
        process.wait()

# --------------------------------------------------------------------------------------------------
# Supervisor
# --------------------------------------------------------------------------------------------------
def main() -> int:
    """Start and supervise the backend and frontend applications."""
    # Child processes
    backend_process: subprocess.Popen[bytes] | None = None
    frontend_process: subprocess.Popen[bytes] | None = None
    try:
        # Backend startup
        backend_process = start_process("src.backend")
        exit_code = wait_for_backend(backend_process)
        if exit_code is not None:
            return exit_code
        # Frontend startup
        frontend_process = start_process("src.frontend")
        # Runtime monitoring
        return wait_for_first_process_exit((backend_process, frontend_process))
    except KeyboardInterrupt:
        # User interruption
        return 130
    except Exception as exc:
        # Supervisor failure
        print(f"Could not run {APP_NAME}: {exc}", file=sys.stderr)
        return 1
    finally:
        # Child cleanup
        stop_process(frontend_process)
        stop_process(backend_process)

# --------------------------------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    raise SystemExit(main())
