from __future__ import annotations

from datetime import datetime


def seconds_until(target: datetime, now: datetime | None = None) -> float:
    current = now or (
        datetime.now(target.tzinfo) if target.tzinfo else datetime.now()
    )
    if target.tzinfo is None and current.tzinfo is not None:
        current = current.replace(tzinfo=None)
    elif target.tzinfo is not None and current.tzinfo is None:
        current = current.replace(tzinfo=target.tzinfo)
    return max(0.0, (target - current).total_seconds())


def format_countdown(seconds: float) -> str:
    remaining = max(0, int(seconds))
    days, remaining = divmod(remaining, 86_400)
    hours, remaining = divmod(remaining, 3_600)
    minutes, secs = divmod(remaining, 60)

    if days:
        return f"{days}天 {hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
