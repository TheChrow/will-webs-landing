from datetime import UTC, datetime


def utcnow() -> datetime:
    """Ahora en UTC, naive (la base de datos guarda DATETIME en UTC sin zona)."""
    return datetime.now(UTC).replace(tzinfo=None)
