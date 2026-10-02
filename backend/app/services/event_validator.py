"""Event ID validation — event IDs are exactly 2 digits (00-99)."""
import re

_EVENT_ID_RE = re.compile(r"^\d{2}$")


def validate_event_id(raw: str) -> tuple[bool, str | None]:
    """Return (is_valid, error_message). Event IDs are exactly 2 digits."""
    if not raw or not str(raw).strip():
        return False, "Event ID is required"
    value = str(raw).strip()
    if not _EVENT_ID_RE.match(value):
        return False, "Event ID must be exactly 2 digits (00-99)"
    return True, None
