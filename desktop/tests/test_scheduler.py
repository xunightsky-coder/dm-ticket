from datetime import datetime, timedelta

from dm_ticket_assistant.scheduler import format_countdown, seconds_until


def test_seconds_until_returns_remaining_seconds() -> None:
    now = datetime(2026, 11, 1, 10, 0, 0)
    target = now + timedelta(seconds=90)
    assert seconds_until(target, now) == 90


def test_seconds_until_never_returns_negative() -> None:
    now = datetime(2026, 11, 1, 10, 0, 0)
    assert seconds_until(now - timedelta(seconds=1), now) == 0


def test_format_countdown() -> None:
    assert format_countdown(3661) == "01:01:01"
    assert format_countdown(90061) == "1天 01:01:01"
