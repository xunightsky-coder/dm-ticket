from __future__ import annotations

import json
import os
from pathlib import Path

from .models import TicketTask


def default_config_path() -> Path:
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / ".config"
    return base / "DMTicketAssistant" / "task.json"


def save_task(task: TicketTask, path: Path | None = None) -> Path:
    task.validate()
    destination = path or default_config_path()
    destination.parent.mkdir(parents=True, exist_ok=True)

    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(task.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(destination)
    return destination


def load_task(path: Path | None = None) -> TicketTask | None:
    source = path or default_config_path()
    if not source.exists():
        return None

    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("任务配置文件格式无效。")
    return TicketTask.from_dict(payload)
