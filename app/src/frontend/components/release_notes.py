"""Release-note presentation helpers."""

import html
from datetime import datetime

from src.contracts.artifacts.releases import ReleaseEntry

# --------------------------------------------------------------------------------------------------
# Formatting
# --------------------------------------------------------------------------------------------------
def format_release_entries_html(releases: list[ReleaseEntry]) -> str:
    """Format release entries as a small HTML document."""
    if not releases:
        return "<!doctype html><html><body><p>No release notes available.</p></body></html>"
    parts = ["<!doctype html>", "<html>", "<body>"]
    for release in reversed(releases):
        version = html.escape(release.version)
        created_at_local = html.escape(_format_release_datetime_local(release.created_at_utc))
        parts.append(f"<h2>Version {version}</h2>")
        parts.append(f"<p><code>{created_at_local}</code></p>")
        if release.changes:
            parts.append("<ul>")
            parts.extend(f"<li>{html.escape(change)}</li>" for change in release.changes)
            parts.append("</ul>")
        else:
            parts.append("<p>No changes listed.</p>")
    parts.extend(["</body>", "</html>"])
    return "\n".join(parts)

# --------------------------------------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------------------------------------
def _format_release_datetime_local(value: datetime) -> str:
    return value.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
