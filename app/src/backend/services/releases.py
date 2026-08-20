"""Release discovery and application-update service."""

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from src.backend.utils.paths import PENDING_UPDATE_FILE_PATH
from src.backend.utils.tmp import create_file, get_tmp_file_path
from src.config import (
    RELEASE_DOWNLOAD_TIMEOUT_SECONDS,
    RELEASE_HTTP_USER_AGENT,
    RELEASE_REMOTE_REQUEST_TIMEOUT_SECONDS,
    RELEASE_REPOSITORY_NAME,
)
from src.contracts.releases import (
    PendingReleaseUpdate,
    ReleaseMetadata,
    ReleaseStageResponse,
    ReleaseUpdateResponse,
)
from src.utils.logging import logger
from src.utils.paths import PROJECT_DIR, PYPROJECT_FILE_PATH
from src.utils.versions import get_pyproject_version, is_version_newer

# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------
GITHUB_LATEST_RELEASE_API_URL = (
    f"https://api.github.com/repos/{RELEASE_REPOSITORY_NAME}/releases/latest"
)

# --------------------------------------------------------------------------------------------------
# Internal models
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class _ReleaseAsset:
    """GitHub release asset download information."""

    name: str
    download_url: str
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class _ResolvedRelease:
    """Validated metadata and archive location for the latest GitHub release."""

    metadata: ReleaseMetadata
    archive_asset: _ReleaseAsset

# --------------------------------------------------------------------------------------------------
# Release discovery
# --------------------------------------------------------------------------------------------------
def get_latest_release_update() -> ReleaseUpdateResponse:
    """Return the latest published release compared with the installed version."""
    current_version = get_pyproject_version(PYPROJECT_FILE_PATH)
    logger.info(f"Checking for updates. Current version: {current_version}")
    resolved_release = _resolve_latest_release()
    latest_version = resolved_release.metadata.version
    logger.info(f"Latest published version: {latest_version}")
    return ReleaseUpdateResponse(
        current_version=current_version,
        latest_version=latest_version,
        is_update_available=is_version_newer(latest_version, current_version),
        is_git_repository=is_git_repository(),
        releases=resolved_release.metadata.releases,
    )

# --------------------------------------------------------------------------------------------------
# Update preparation
# --------------------------------------------------------------------------------------------------
def stage_latest_release_update() -> ReleaseStageResponse:
    """Download and validate the latest release for the external update script."""
    if is_git_repository():
        raise ValueError("In-app updates are disabled in a Git repository.")
    PENDING_UPDATE_FILE_PATH.unlink(missing_ok=True)
    current_version = get_pyproject_version(PYPROJECT_FILE_PATH)
    resolved_release = _resolve_latest_release()
    metadata = resolved_release.metadata
    if not is_version_newer(metadata.version, current_version):
        raise ValueError(f"Version {metadata.version} is not newer than {current_version}.")
    logger.info(f"Preparing release update: {current_version} -> {metadata.version}")
    archive_file_path = _download_release_asset(resolved_release.archive_asset)
    actual_sha256 = _calculate_file_sha256(archive_file_path)
    if actual_sha256 != metadata.archive_sha256:
        raise ValueError("Downloaded release archive failed SHA-256 verification.")
    pending_update = PendingReleaseUpdate(
        version=metadata.version,
        archive_name=archive_file_path.name,
        archive_sha256=metadata.archive_sha256,
    )
    create_file(
        PENDING_UPDATE_FILE_PATH.name,
        pending_update.model_dump_json(indent=2) + "\n",
    )
    logger.info(f"Release update ready to apply: {metadata.version}")
    return ReleaseStageResponse(version=metadata.version)

# --------------------------------------------------------------------------------------------------
# Installation type
# --------------------------------------------------------------------------------------------------
def is_git_repository() -> bool:
    """Return whether the application is running from a Git repository."""
    return (PROJECT_DIR / ".git").exists()

# --------------------------------------------------------------------------------------------------
# Internal requests
# --------------------------------------------------------------------------------------------------
def _resolve_latest_release() -> _ResolvedRelease:
    release_data = _read_json_url(GITHUB_LATEST_RELEASE_API_URL)
    metadata_asset = _get_release_asset(release_data, ".json")
    archive_asset = _get_release_asset(release_data, ".zip")
    metadata = _read_release_metadata(metadata_asset)
    return _ResolvedRelease(metadata=metadata, archive_asset=archive_asset)
# --------------------------------------------------------------------------------------------------
def _read_json_url(url: str) -> dict[str, object]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": RELEASE_HTTP_USER_AGENT,
        },
    )
    try:
        with urlopen(request, timeout=RELEASE_REMOTE_REQUEST_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Could not fetch the latest release from {RELEASE_REPOSITORY_NAME}."
        ) from exc
    if not isinstance(data, dict):
        raise ValueError("Latest release metadata must contain an object.")
    return data
# --------------------------------------------------------------------------------------------------
def _read_release_metadata(asset: _ReleaseAsset) -> ReleaseMetadata:
    request = Request(
        asset.download_url,
        headers={
            "Accept": "application/octet-stream",
            "User-Agent": RELEASE_HTTP_USER_AGENT,
        },
    )
    try:
        with urlopen(request, timeout=RELEASE_REMOTE_REQUEST_TIMEOUT_SECONDS) as response:
            return ReleaseMetadata.model_validate_json(response.read())
    except (HTTPError, URLError, TimeoutError, OSError, ValidationError) as exc:
        raise RuntimeError(f"Could not read release metadata: {asset.name}") from exc
# --------------------------------------------------------------------------------------------------
def _download_release_asset(asset: _ReleaseAsset) -> Path:
    output_file_path = get_tmp_file_path(asset.name)
    request = Request(
        asset.download_url,
        headers={
            "Accept": "application/octet-stream",
            "User-Agent": RELEASE_HTTP_USER_AGENT,
        },
    )
    logger.info(f"Downloading release asset: {asset.name}")
    try:
        with (
            urlopen(request, timeout=RELEASE_DOWNLOAD_TIMEOUT_SECONDS) as response,
            output_file_path.open("wb") as output_file,
        ):
            shutil.copyfileobj(response, output_file)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Could not download release asset: {asset.name}") from exc
    return output_file_path

# --------------------------------------------------------------------------------------------------
# Internal validation
# --------------------------------------------------------------------------------------------------
def _get_release_asset(release_data: dict[str, object], file_suffix: str) -> _ReleaseAsset:
    assets = release_data.get("assets")
    if not isinstance(assets, list):
        raise ValueError("Latest GitHub release does not contain an assets list.")
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = asset.get("name")
        download_url = asset.get("browser_download_url")
        if (
            isinstance(name, str)
            and Path(name).name == name
            and isinstance(download_url, str)
            and name.endswith(file_suffix)
        ):
            return _ReleaseAsset(name=name, download_url=download_url)
    raise ValueError(f"Latest GitHub release does not contain a {file_suffix} asset.")
# --------------------------------------------------------------------------------------------------
def _calculate_file_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as input_file:
        for block in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
