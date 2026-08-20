"""Developer helpers for creating application releases."""

import hashlib
import re
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from src.config import RELEASE_ARCHIVE_PREFIX
from src.contracts.artifacts.releases import ReleaseEntry, ReleaseHistory, ReleaseMetadata
from src.utils.versions import PYPROJECT_VERSION_RE, get_pyproject_version, parse_semantic_version

# --------------------------------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------------------------------
UV_LOCK_PROJECT_VERSION_RE = re.compile(
    r'(?ms)^(?P<prefix>\[\[package\]\]\nname\s*=\s*"oscilloscope-studio"\nversion\s*=\s*")'
    r'(?P<version>\d+\.\d+\.\d+)'
    r'(?P<suffix>"\s*)$'
)

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
    output_file_path: Path,
    version: str,
    archive_sha256: str,
    releases: list[ReleaseEntry],
) -> Path:
    """Write validated updater metadata as JSON."""
    metadata = ReleaseMetadata(
        version=version,
        archive_sha256=archive_sha256,
        created_at_utc=datetime.now(UTC),
        releases=releases,
    )
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    output_file_path.write_text(
        metadata.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return output_file_path

# --------------------------------------------------------------------------------------------------
# Release history
# --------------------------------------------------------------------------------------------------
def get_release_entries(releases_file_path: Path) -> list[ReleaseEntry]:
    """Return release entries from the project release-history file."""
    return _read_release_history(releases_file_path).releases
# --------------------------------------------------------------------------------------------------
def append_release_entry(releases_file_path: Path, version: str, changes: list[str]) -> Path:
    """Append a release entry to the project release-history file."""
    release_history = _read_release_history(releases_file_path)
    release_history.releases.append(
        ReleaseEntry(
            version=version,
            created_at_utc=datetime.now(UTC),
            changes=changes,
        )
    )
    releases_file_path.write_text(
        release_history.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return releases_file_path
# --------------------------------------------------------------------------------------------------
def _read_release_history(releases_file_path: Path) -> ReleaseHistory:
    if not releases_file_path.exists():
        return ReleaseHistory(releases=[])
    try:
        return ReleaseHistory.model_validate_json(releases_file_path.read_bytes())
    except ValidationError as exc:
        raise ValueError(f"Invalid releases JSON: {releases_file_path}") from exc
# --------------------------------------------------------------------------------------------------
def _is_hidden_path(file_path: Path) -> bool:
    return any(part.startswith(".") for part in file_path.parts)
