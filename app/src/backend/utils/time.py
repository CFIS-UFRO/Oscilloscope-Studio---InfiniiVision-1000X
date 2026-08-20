"""Backend time formatting utilities."""

# --------------------------------------------------------------------------------------------------
# Duration formatting
# --------------------------------------------------------------------------------------------------
def format_duration(seconds: float) -> str:
    """Format a duration using the most appropriate time unit."""
    absolute_seconds = abs(seconds)
    if absolute_seconds < 1:
        return f"{seconds * 1000:.1f} ms"
    if absolute_seconds < 60:
        return f"{seconds:.1f} s"
    if absolute_seconds < 3600:
        return f"{seconds / 60:.1f} m"
    return f"{seconds / 3600:.1f} h"
