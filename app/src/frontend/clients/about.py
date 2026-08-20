"""Backend About-information client."""

from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from pydantic import ValidationError

from src.config import BACKEND_REQUEST_TIMEOUT_SECONDS, BACKEND_URL
from src.contracts.api.about import AboutResponse

# --------------------------------------------------------------------------------------------------
# Endpoint
# --------------------------------------------------------------------------------------------------
ABOUT_URL = f"{BACKEND_URL}/api/v1/about"

# --------------------------------------------------------------------------------------------------
# Requests
# --------------------------------------------------------------------------------------------------
def get_about_info() -> AboutResponse:
    """Request and validate application About information from the backend."""
    try:
        with urlopen(ABOUT_URL, timeout=BACKEND_REQUEST_TIMEOUT_SECONDS) as response:
            return AboutResponse.model_validate_json(response.read())
    except (HTTPError, URLError, TimeoutError, OSError, ValidationError) as exc:
        raise RuntimeError("Could not load About information from the backend.") from exc
# --------------------------------------------------------------------------------------------------
def get_about_logo(logo_path: str) -> bytes:
    """Download an About logo from a backend-relative path."""
    if not logo_path.startswith("/api/v1/about/logos/"):
        raise ValueError(f"Invalid About logo path: {logo_path}")
    try:
        with urlopen(
            f"{BACKEND_URL}{logo_path}",
            timeout=BACKEND_REQUEST_TIMEOUT_SECONDS,
        ) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Could not load About logo: {logo_path}") from exc
