"""Backend release API client."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from src.config import (
    BACKEND_URL,
    RELEASE_CHECK_TIMEOUT_SECONDS,
    RELEASE_STAGE_TIMEOUT_SECONDS,
)
from src.contracts.api.releases import ReleaseStageResponse, ReleaseUpdateResponse

# --------------------------------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------------------------------
LATEST_RELEASE_URL = f"{BACKEND_URL}/api/v1/releases/latest"
STAGE_LATEST_RELEASE_URL = f"{BACKEND_URL}/api/v1/releases/latest/stage"

# --------------------------------------------------------------------------------------------------
# Requests
# --------------------------------------------------------------------------------------------------
def get_latest_release_update() -> ReleaseUpdateResponse:
    """Request and validate the latest release information from the backend."""
    try:
        with urlopen(LATEST_RELEASE_URL, timeout=RELEASE_CHECK_TIMEOUT_SECONDS) as response:
            return ReleaseUpdateResponse.model_validate_json(response.read())
    except HTTPError as exc:
        raise RuntimeError(_get_http_error_detail(exc, "Could not check for updates.")) from exc
    except (URLError, TimeoutError, OSError, ValidationError) as exc:
        raise RuntimeError("Could not check for updates through the backend.") from exc
# --------------------------------------------------------------------------------------------------
def stage_latest_release_update() -> ReleaseStageResponse:
    """Ask the backend to prepare the latest application release for installation."""
    request = Request(STAGE_LATEST_RELEASE_URL, method="POST")
    try:
        with urlopen(request, timeout=RELEASE_STAGE_TIMEOUT_SECONDS) as response:
            return ReleaseStageResponse.model_validate_json(response.read())
    except HTTPError as exc:
        raise RuntimeError(_get_http_error_detail(exc, "Could not prepare the update.")) from exc
    except (URLError, TimeoutError, OSError, ValidationError) as exc:
        raise RuntimeError("Could not prepare the update through the backend.") from exc

# --------------------------------------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------------------------------------
def _get_http_error_detail(error: HTTPError, fallback_message: str) -> str:
    try:
        body = json.loads(error.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return fallback_message
    detail = body.get("detail") if isinstance(body, dict) else None
    return detail if isinstance(detail, str) else fallback_message
