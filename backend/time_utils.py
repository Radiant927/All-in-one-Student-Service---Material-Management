from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return an aware UTC datetime for new tables and token expiry."""
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    """Compatibility helper for legacy tables that still store ISO strings."""
    return utcnow().isoformat()

