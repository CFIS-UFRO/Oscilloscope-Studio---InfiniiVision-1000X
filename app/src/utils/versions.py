"""Shared semantic-version and project-version helpers."""

import re
from pathlib import Path

from src.utils.paths import PYPROJECT_FILE_PATH

# --------------------------------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------------------------------
SEMANTIC_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
PYPROJECT_VERSION_RE = re.compile(
    r'(?m)^(?P<prefix>version\s*=\s*")(?P<version>\d+\.\d+\.\d+)(?P<suffix>"\s*)$'
)

# --------------------------------------------------------------------------------------------------
# Versions
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
def get_pyproject_version(pyproject_file_path: Path | None = None) -> str:
    """Read the project version from pyproject.toml."""
    if pyproject_file_path is None:
        pyproject_file_path = PYPROJECT_FILE_PATH
    content = pyproject_file_path.read_text(encoding="utf-8")
    match = PYPROJECT_VERSION_RE.search(content)
    if match is None:
        raise ValueError(f"Could not find a semantic version in {pyproject_file_path}.")
    return match.group("version")
