from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from urllib.parse import parse_qs, urlparse


def is_damai_url(url: str) -> bool:
    """Return True only for HTTPS URLs on a Damai domain."""
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False

    host = (parsed.hostname or "").lower()
    return (
        parsed.scheme.lower() == "https"
        and (host == "damai.cn" or host.endswith(".damai.cn"))
    )


def item_id_from_url(url: str) -> str:
    try:
        values = parse_qs(urlparse(url.strip()).query).get("itemId", [])
    except ValueError:
        return ""
    return values[0].strip() if values else ""


@dataclass(slots=True)
class PriorityOption:
    session: str = ""
    ticket_tier: str = ""
    price: str = ""

    def validate(self) -> None:
        if bool(self.session.strip()) != bool(self.ticket_tier.strip()):
            raise ValueError("优先级设置中，场次和票档需要同时填写。")


@dataclass(slots=True)
class TicketTask:
    event_name: str = ""
    event_url: str = ""
    item_id: str = ""
    sale_time: str = ""
    quantity: int = 1
    priorities: list[PriorityOption] = field(default_factory=list)
    notes: str = ""

    def validate(self) -> None:
        url = self.event_url.strip()
        item_id = self.item_id.strip()

        if url and not is_damai_url(url):
            raise ValueError("详情页 URL 必须是 HTTPS 的 damai.cn 官方域名。")

        if not item_id and url:
            item_id = item_id_from_url(url)

        if not item_id and not url:
            raise ValueError("请填写大麦详情页 URL 或 Item ID。")

        if item_id and not item_id.isdigit():
            raise ValueError("Item ID 只能包含数字。")

        if not 1 <= self.quantity <= 20:
            raise ValueError("购买数量必须在 1 到 20 之间。")

        if self.sale_time:
            try:
                datetime.fromisoformat(self.sale_time)
            except ValueError as exc:
                raise ValueError("开售时间格式无效，请重新选择时间。") from exc

        for option in self.priorities:
            option.validate()

    @classmethod
    def from_dict(cls, payload: dict) -> "TicketTask":
        priorities = [
            PriorityOption(
                session=str(item.get("session", "")),
                ticket_tier=str(item.get("ticket_tier", "")),
                price=str(item.get("price", "")),
            )
            for item in payload.get("priorities", [])
            if isinstance(item, dict)
        ]
        return cls(
            event_name=str(payload.get("event_name", "")),
            event_url=str(payload.get("event_url", "")),
            item_id=str(payload.get("item_id", "")),
            sale_time=str(payload.get("sale_time", "")),
            quantity=int(payload.get("quantity", 1)),
            priorities=priorities,
            notes=str(payload.get("notes", "")),
        )

    def to_dict(self) -> dict:
        return asdict(self)
