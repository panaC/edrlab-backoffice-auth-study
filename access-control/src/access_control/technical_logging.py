from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any


def technical_log(event: str, *, component: str, **fields: Any) -> None:
    record = {
        "occurredAt": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "component": component,
        "event": event,
    }
    record.update({key: _json_safe(value) for key, value in fields.items() if value is not None})
    print(json.dumps(record, sort_keys=True, separators=(",", ":")), file=sys.stderr, flush=True)


def elapsed_ms(started: float, ended: float) -> float:
    return round((ended - started) * 1000, 3)


def _json_safe(value: Any) -> Any:
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return str(value)
