"""HTML viewer presentation settings."""

from dataclasses import dataclass

# --------------------------------------------------------------------------------------------------
# Style
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class HtmlViewerStyle:
    """Configure optional HTML viewer document styles."""

    include_links: bool = False
    include_h1: bool = False
    h2_margin: str = "0 0 8px"
