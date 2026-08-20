"""General backend API client."""

from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from pydantic import ValidationError

from src.config import BACKEND_REQUEST_TIMEOUT_SECONDS, BACKEND_URL
from src.contracts.general import ApplicationInfoResponse

# --------------------------------------------------------------------------------------------------
# Endpoint
# --------------------------------------------------------------------------------------------------
APPLICATION_INFO_URL = f"{BACKEND_URL}/api/v1/info"

# --------------------------------------------------------------------------------------------------
# Requests
# --------------------------------------------------------------------------------------------------
def get_application_info() -> ApplicationInfoResponse:
    """Request and validate general information from the backend."""
    try:
        with urlopen(APPLICATION_INFO_URL, timeout=BACKEND_REQUEST_TIMEOUT_SECONDS) as response:
            return ApplicationInfoResponse.model_validate_json(response.read())
    except (HTTPError, URLError, TimeoutError, OSError, ValidationError) as exc:
        raise RuntimeError("Could not load application information from the backend.") from exc
