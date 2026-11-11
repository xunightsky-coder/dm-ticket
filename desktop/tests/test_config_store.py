from pathlib import Path

import pytest

from dm_ticket_assistant.config_store import load_task, save_task
from dm_ticket_assistant.models import PriorityOption, TicketTask


def test_save_and_load_task_round_trip(tmp_path: Path) -> None:
    original = TicketTask(
        event_name="测试演出",
        item_id="123456",
        quantity=2,
        priorities=[PriorityOption("周五", "看台", "680")],
        notes="提前准备好 App",
    )

    destination = save_task(original, tmp_path / "task.json")
    restored = load_task(destination)

    assert restored == original


def test_load_task_returns_none_for_missing_file(tmp_path: Path) -> None:
    assert load_task(tmp_path / "missing.json") is None


def test_load_task_rejects_non_object_json(tmp_path: Path) -> None:
    source = tmp_path / "invalid.json"
    source.write_text("[]", encoding="utf-8")

    with pytest.raises(TypeError, match="配置文件格式无效"):
        load_task(source)
