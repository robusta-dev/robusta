from datetime import datetime, timezone


def current_utc_timestamp() -> datetime:
    return datetime.now(timezone.utc)