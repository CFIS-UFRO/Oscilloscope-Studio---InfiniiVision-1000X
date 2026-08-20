"""Apply a backend-prepared update after the application processes stop."""

import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

from pydantic import ValidationError

from src.config import APP_NAME
from src.contracts.updater import PendingReleaseUpdate

# --------------------------------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------------------------------
APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = APP_DIR.parent
TMP_DIR = APP_DIR / "tmp"
PENDING_UPDATE_FILE_PATH = TMP_DIR / "pending_update.json"

# --------------------------------------------------------------------------------------------------
# Update application
# --------------------------------------------------------------------------------------------------
def main() -> int:
    """Validate and apply the update prepared by the backend."""
    try:
        pending_update = _read_pending_update()
        archive_file_path = _resolve_archive_file_path(pending_update.archive_name)
        actual_sha256 = _calculate_file_sha256(archive_file_path)
        if actual_sha256 != pending_update.archive_sha256:
            raise ValueError("Prepared release archive failed SHA-256 verification.")
        print(f"Applying {APP_NAME} {pending_update.version}...")
        _extract_release_archive(archive_file_path, PROJECT_DIR)
    except (OSError, ValueError, ValidationError, zipfile.BadZipFile) as exc:
        print(f"Could not apply release update: {exc}", file=sys.stderr)
        return 1
    _clean_update_files(archive_file_path)
    print(f"{APP_NAME} {pending_update.version} was installed successfully.")
    return 0
# --------------------------------------------------------------------------------------------------
def _read_pending_update() -> PendingReleaseUpdate:
    if not PENDING_UPDATE_FILE_PATH.is_file():
        raise ValueError("No prepared release update was found.")
    return PendingReleaseUpdate.model_validate_json(PENDING_UPDATE_FILE_PATH.read_bytes())
# --------------------------------------------------------------------------------------------------
def _resolve_archive_file_path(archive_name: str) -> Path:
    if not archive_name or Path(archive_name).name != archive_name:
        raise ValueError(f"Invalid prepared release archive name: {archive_name}")
    archive_file_path = (TMP_DIR / archive_name).resolve()
    if archive_file_path.parent != TMP_DIR.resolve() or not archive_file_path.is_file():
        raise ValueError(f"Prepared release archive was not found: {archive_name}")
    return archive_file_path
# --------------------------------------------------------------------------------------------------
def _calculate_file_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as input_file:
        for block in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
# --------------------------------------------------------------------------------------------------
def _clean_update_files(archive_file_path: Path) -> None:
    for file_path in (PENDING_UPDATE_FILE_PATH, archive_file_path):
        try:
            file_path.unlink(missing_ok=True)
        except OSError as exc:
            print(f"Could not remove update file {file_path}: {exc}", file=sys.stderr)
# --------------------------------------------------------------------------------------------------
def _extract_release_archive(archive_file_path: Path, destination_dir_path: Path) -> None:
    destination_root = destination_dir_path.resolve()
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

# --------------------------------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    raise SystemExit(main())
