from datetime import datetime

import pytest

from dm_ticket_assistant.models import (
    PriorityOption,
    TicketTask,
    is_damai_url,
    item_id_from_url,
)


def test_accepts_damai_https_subdomain() -> None:
    assert is_damai_url("https://m.damai.cn/damai/detail/item.html?itemId=123456")


@pytest.mark.parametrize(
    "url",
    [
        "http://m.damai.cn/item",
        "https://damai.cn.example.com/item",
        "https://example.com/?next=https://damai.cn",
        "javascript:alert(1)",
    ],
)
def test_rejects_non_damai_or_non_https_urls(url: str) -> None:
    assert not is_damai_url(url)


def test_extracts_item_id_from_url() -> None:
    assert item_id_from_url("https://m.damai.cn/item?itemId=123456") == "123456"


def test_task_requires_url_or_item_id() -> None:
    with pytest.raises(ValueError, match="详情页 URL 或 Item ID"):
        TicketTask().validate()


def test_task_validates_quantity() -> None:
    task = TicketTask(item_id="123456", quantity=0)
    with pytest.raises(ValueError, match="购买数量"):
        task.validate()


def test_priority_requires_session_and_tier_together() -> None:
    task = TicketTask(
        item_id="123456",
        priorities=[PriorityOption(session="周五", ticket_tier="", price="680")],
    )
    with pytest.raises(ValueError, match="场次和票档"):
        task.validate()


def test_task_accepts_valid_configuration() -> None:
    task = TicketTask(
        event_name="测试演出",
        item_id="123456",
        sale_time=datetime(2026, 12, 1, 12, 0).isoformat(),
        quantity=2,
        priorities=[PriorityOption("周五", "看台", "680")],
    )
    task.validate()
    assert task.to_dict()["quantity"] == 2
