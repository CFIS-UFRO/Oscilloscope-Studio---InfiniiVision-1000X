"""Render release-history entries as HTML for display in the GUI."""

import html
from datetime import UTC, datetime

# --------------------------------------------------------------------------------------------------
# HTML rendering
# --------------------------------------------------------------------------------------------------
def format_release_entries_html(releases: list[dict[str, object]]) -> str:
    """Format release entries as a small HTML document."""
    if not releases:
        return "<!doctype html><html><body><p>No release notes available.</p></body></html>"
    parts = ["<!doctype html>", "<html>", "<body>"]
    for release in reversed(releases):
        version = html.escape(str(release.get("version", "Unknown")))
        created_at_local = html.escape(_format_release_datetime_local(release.get("created_at_utc")))
        changes = release.get("changes", [])
        parts.append(f"<h2>Version {version}</h2>")
        if created_at_local:
            parts.append(f"<p><code>{created_at_local}</code></p>")
        if isinstance(changes, list) and changes:
            parts.append("<ul>")
            parts.extend(f"<li>{html.escape(str(change))}</li>" for change in changes)
            parts.append("</ul>")
        else:
            parts.append("<p>No changes listed.</p>")
    parts.extend(["</body>", "</html>"])
    return "\n".join(parts)
# --------------------------------------------------------------------------------------------------
def _format_release_datetime_local(value: object) -> str:
    if not isinstance(value, str) or not value:
        return ""
    try:
        release_datetime = datetime.fromisoformat(value)
    except ValueError:
        return value
    if release_datetime.tzinfo is None:
        release_datetime = release_datetime.replace(tzinfo=UTC)
    return release_datetime.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
