"""Release creation helpers and GitHub-based application updates."""

import hashlib
import re
import shutil
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, StringConstraints, ValidationError, field_serializer

from src.core.config import (
    RELEASE_ARCHIVE_PREFIX,
    RELEASE_HTTP_USER_AGENT,
    RELEASE_REPOSITORY_NAME,
)
from src.core.logging import logger
from src.core.paths import PROJECT_DIR, PYPROJECT_FILE_PATH
from src.core.tmp import create_file, get_tmp_file_path

# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------
GITHUB_LATEST_RELEASE_API_URL = (
    f"https://api.github.com/repos/{RELEASE_REPOSITORY_NAME}/releases/latest"
)
SEMANTIC_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
PYPROJECT_VERSION_RE = re.compile(
    r'(?m)^(?P<prefix>version\s*=\s*")(?P<version>\d+\.\d+\.\d+)(?P<suffix>"\s*)$'
)
UV_LOCK_PROJECT_VERSION_RE = re.compile(
    r'(?ms)^(?P<prefix>\[\[package\]\]\nname\s*=\s*"oscilloscope-studio"\nversion\s*=\s*")'
    r'(?P<version>\d+\.\d+\.\d+)'
    r'(?P<suffix>"\s*)$'
)

# --------------------------------------------------------------------------------------------------
# Data models
# --------------------------------------------------------------------------------------------------
SemanticVersion = Annotated[str, StringConstraints(pattern=r"^\d+\.\d+\.\d+$")]
Sha256Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
# --------------------------------------------------------------------------------------------------
class _InboundModel(BaseModel):
    """Base model for payloads parsed from GitHub or on-disk JSON."""

    @field_serializer("created_at_utc", check_fields=False)
    def _serialize_created_at_utc(self, value: datetime) -> str:
        return value.isoformat()
# --------------------------------------------------------------------------------------------------
class ReleaseEntry(_InboundModel):
    """A single published release and its human-readable changes."""

    version: SemanticVersion
    created_at_utc: datetime
    changes: list[str] = []
# --------------------------------------------------------------------------------------------------
class ReleasesFile(_InboundModel):
    """Contents of the project release-history file."""

    releases: list[ReleaseEntry] = []
# --------------------------------------------------------------------------------------------------
class ReleaseMetadata(_InboundModel):
    """Updater metadata published alongside a release archive."""

    version: SemanticVersion
    archive_sha256: Sha256Digest
    created_at_utc: datetime
    releases: list[ReleaseEntry] = []
# --------------------------------------------------------------------------------------------------
class GitHubAsset(_InboundModel):
    """One downloadable asset attached to a GitHub release."""

    name: str
    browser_download_url: str
# --------------------------------------------------------------------------------------------------
class GitHubRelease(_InboundModel):
    """Subset of the GitHub latest-release API response."""

    assets: list[GitHubAsset] = []
# --------------------------------------------------------------------------------------------------
class ReleaseAsset(BaseModel):
    """GitHub release asset download information."""

    name: str
    download_url: str
# --------------------------------------------------------------------------------------------------
class ReleaseUpdate(BaseModel):
    """Resolved update metadata for the latest published release."""

    current_version: SemanticVersion
    latest_version: SemanticVersion
    archive_sha256: Sha256Digest
    metadata_asset: ReleaseAsset
    archive_asset: ReleaseAsset
    releases: list[ReleaseEntry] = []

    @property
    def is_update_available(self) -> bool:
        """Return whether the published release is newer than the installed version."""
        return is_version_newer(self.latest_version, self.current_version)

# --------------------------------------------------------------------------------------------------
# Versions
# --------------------------------------------------------------------------------------------------
def increment_version(version: str, update_type: str) -> str:
    """Increment a semantic version using major, minor, or bugfix update types."""
    normalized_update_type = update_type.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized_update_type not in {"major", "minor", "bugfix"}:
        raise ValueError("Update type must be major, minor, or bugfix.")
    major, minor, bugfix = parse_semantic_version(version)
    if normalized_update_type == "major":
        return f"{major + 1}.0.0"
    if normalized_update_type == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{bugfix + 1}"
# --------------------------------------------------------------------------------------------------
def parse_semantic_version(version: str) -> tuple[int, int, int]:
    """Parse a three-part semantic version into a comparable tuple."""
    if SEMANTIC_VERSION_RE.fullmatch(version) is None:
        raise ValueError(f"Invalid semantic version: {version}")
    major, minor, bugfix = version.split(".")
    return int(major), int(minor), int(bugfix)
# --------------------------------------------------------------------------------------------------
def is_version_newer(candidate_version: str, current_version: str) -> bool:
    """Return whether the candidate version is newer than the current version."""
    return parse_semantic_version(candidate_version) > parse_semantic_version(current_version)
# --------------------------------------------------------------------------------------------------
def get_pyproject_version(pyproject_file_path: Path) -> str:
    """Read the project version from pyproject.toml."""
    content = pyproject_file_path.read_text(encoding="utf-8")
    match = PYPROJECT_VERSION_RE.search(content)
    if match is None:
        raise ValueError(f"Could not find a semantic version in {pyproject_file_path}.")
    return match.group("version")
# --------------------------------------------------------------------------------------------------
def update_pyproject_version(pyproject_file_path: Path, uv_lock_file_path: Path, update_type: str) -> str:
    """Increment and write the project version in pyproject.toml and uv.lock."""
    current_version = get_pyproject_version(pyproject_file_path)
    new_version = increment_version(current_version, update_type)
    file_updates = []
    for file_path, version_re in (
        (pyproject_file_path, PYPROJECT_VERSION_RE),
        (uv_lock_file_path, UV_LOCK_PROJECT_VERSION_RE),
    ):
        file_updates.append((file_path, _get_updated_version_content(file_path, version_re, new_version)))
    for file_path, updated_content in file_updates:
        file_path.write_text(updated_content, encoding="utf-8")
    return new_version
# --------------------------------------------------------------------------------------------------
def _get_updated_version_content(
    file_path: Path,
    version_re: re.Pattern[str],
    new_version: str,
) -> str:
    content = file_path.read_text(encoding="utf-8")
    if version_re.search(content) is None:
        raise ValueError(f"Could not find a semantic version in {file_path}.")
    return version_re.sub(rf"\g<prefix>{new_version}\g<suffix>", content, count=1)

# --------------------------------------------------------------------------------------------------
# Release files
# --------------------------------------------------------------------------------------------------
def get_release_file_stem(version: str) -> str:
    """Return the release file name without an extension."""
    parse_semantic_version(version)
    return f"{RELEASE_ARCHIVE_PREFIX}_{version}"
# --------------------------------------------------------------------------------------------------
def get_git_managed_file_paths(project_dir_path: Path) -> list[Path]:
    """Return tracked and untracked non-ignored project files using Git exclude rules."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=project_dir_path,
        check=True,
        capture_output=True,
        text=True,
    )
    file_paths = []
    for line in result.stdout.splitlines():
        relative_file_path = Path(line)
        if _is_hidden_path(relative_file_path):
            continue
        absolute_file_path = project_dir_path / relative_file_path
        if absolute_file_path.is_file():
            file_paths.append(absolute_file_path)
    return sorted(file_paths, key=lambda path: path.as_posix())
# --------------------------------------------------------------------------------------------------
def compress_paths(source_dir_path: Path, file_paths: list[Path], output_file_path: Path) -> Path:
    """Create a maximum-compression zip archive from project-relative paths."""
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output_file_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for file_path in file_paths:
            archive.write(file_path, arcname=file_path.relative_to(source_dir_path).as_posix())
    return output_file_path
# --------------------------------------------------------------------------------------------------
def calculate_file_sha256(file_path: Path) -> str:
    """Return the lowercase SHA-256 digest for a file."""
    digest = hashlib.sha256()
    with file_path.open("rb") as input_file:
        for block in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
# --------------------------------------------------------------------------------------------------
def write_release_metadata(
    output_relative_path: str,
    version: str,
    archive_sha256: str,
    releases: list[ReleaseEntry],
) -> Path:
    """Write updater metadata as JSON under the project temporary directory."""
    metadata = ReleaseMetadata(
        version=version,
        archive_sha256=archive_sha256,
        created_at_utc=datetime.now(UTC),
        releases=releases,
    )
    return create_file(output_relative_path, metadata.model_dump_json(indent=2) + "\n")
# --------------------------------------------------------------------------------------------------
def get_release_entries(releases_file_path: Path) -> list[ReleaseEntry]:
    """Return release entries from the project release-history file."""
    return _read_releases_file(releases_file_path).releases
# --------------------------------------------------------------------------------------------------
def append_release_entry(releases_file_path: Path, version: str, changes: list[str]) -> Path:
    """Append a release entry to the project release-history file."""
    releases_file = _read_releases_file(releases_file_path)
    releases_file.releases.append(
        ReleaseEntry(version=version, created_at_utc=datetime.now(UTC), changes=changes)
    )
    releases_file_path.write_text(
        releases_file.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    return releases_file_path

# --------------------------------------------------------------------------------------------------
# Application updates
# --------------------------------------------------------------------------------------------------
def get_latest_release_update() -> ReleaseUpdate:
    """Download the latest metadata asset and resolve available update information."""
    current_version = get_pyproject_version(PYPROJECT_FILE_PATH)
    logger.info(f"Checking for updates. Current version: {current_version}")
    release = _fetch_latest_github_release()
    metadata_asset = _select_release_asset(release, ".json")
    archive_asset = _select_release_asset(release, ".zip")
    metadata_file_path = download_release_asset(metadata_asset)
    metadata = _read_release_metadata(metadata_file_path)
    logger.info(f"Latest published version: {metadata.version}")
    return ReleaseUpdate(
        current_version=current_version,
        latest_version=metadata.version,
        archive_sha256=metadata.archive_sha256,
        metadata_asset=metadata_asset,
        archive_asset=archive_asset,
        releases=metadata.releases,
    )
# --------------------------------------------------------------------------------------------------
def download_release_asset(asset: ReleaseAsset) -> Path:
    """Download a release asset into the application temporary directory."""
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
        with urlopen(request, timeout=120) as response, output_file_path.open("wb") as output_file:
            shutil.copyfileobj(response, output_file)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Could not download release asset: {asset.name}") from exc
    return output_file_path
# --------------------------------------------------------------------------------------------------
def install_release_update(release_update: ReleaseUpdate) -> Path:
    """Download, verify, and extract the selected update into the project root."""
    logger.info(
        f"Installing release update: {release_update.current_version} -> "
        f"{release_update.latest_version}"
    )
    archive_file_path = download_release_asset(release_update.archive_asset)
    actual_sha256 = calculate_file_sha256(archive_file_path)
    if actual_sha256 != release_update.archive_sha256:
        raise ValueError("Downloaded release archive failed SHA-256 verification.")
    extract_release_archive(archive_file_path, PROJECT_DIR)
    logger.info(f"Installed release update: {release_update.latest_version}")
    return archive_file_path
# --------------------------------------------------------------------------------------------------
def extract_release_archive(archive_file_path: Path, destination_dir_path: Path) -> None:
    """Extract an update archive with path-traversal protection."""
    destination_dir_path.mkdir(parents=True, exist_ok=True)
    destination_root = destination_dir_path.resolve()
    logger.info(f"Extracting release archive: {archive_file_path} -> {destination_root}")
    try:
        with zipfile.ZipFile(archive_file_path, mode="r") as archive:
            for member in archive.infolist():
                target_path = (destination_root / member.filename).resolve()
                if target_path != destination_root and destination_root not in target_path.parents:
                    raise ValueError(f"Unsafe archive path: {member.filename}")
                if member.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                    continue
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member, mode="r") as source_file, target_path.open("wb") as output_file:
                    shutil.copyfileobj(source_file, output_file)
                permissions = member.external_attr >> 16
                if permissions:
                    target_path.chmod(permissions)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"Invalid release archive: {archive_file_path}") from exc

# --------------------------------------------------------------------------------------------------
# Internal parsing
# --------------------------------------------------------------------------------------------------
def _fetch_latest_github_release() -> GitHubRelease:
    request = Request(
        GITHUB_LATEST_RELEASE_API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": RELEASE_HTTP_USER_AGENT,
        },
    )
    try:
        with urlopen(request, timeout=60) as response:
            payload = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(
            f"Could not fetch the latest release from {RELEASE_REPOSITORY_NAME}."
        ) from exc
    try:
        return GitHubRelease.model_validate_json(payload)
    except ValidationError as exc:
        raise ValueError("Latest GitHub release response is not in the expected format.") from exc
# --------------------------------------------------------------------------------------------------
def _select_release_asset(release: GitHubRelease, file_suffix: str) -> ReleaseAsset:
    for asset in release.assets:
        if asset.name.endswith(file_suffix):
            return ReleaseAsset(name=asset.name, download_url=asset.browser_download_url)
    raise ValueError(f"Latest GitHub release does not contain a {file_suffix} asset.")
# --------------------------------------------------------------------------------------------------
def _read_release_metadata(metadata_file_path: Path) -> ReleaseMetadata:
    try:
        return ReleaseMetadata.model_validate_json(
            metadata_file_path.read_text(encoding="utf-8")
        )
    except ValidationError as exc:
        raise ValueError(f"Invalid release metadata: {metadata_file_path}") from exc
# --------------------------------------------------------------------------------------------------
def _read_releases_file(releases_file_path: Path) -> ReleasesFile:
    if not releases_file_path.exists():
        return ReleasesFile()
    try:
        return ReleasesFile.model_validate_json(releases_file_path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise ValueError(f"Invalid releases file: {releases_file_path}") from exc
# --------------------------------------------------------------------------------------------------
def _is_hidden_path(file_path: Path) -> bool:
    return any(part.startswith(".") for part in file_path.parts)
