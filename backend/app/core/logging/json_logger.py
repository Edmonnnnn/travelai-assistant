from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(level: str, event: str, **fields: Any) -> None:
    """
    Minimal JSON logger: prints one JSON line to stdout.
    Do NOT include PII in fields.
    """
    payload: Dict[str, Any] = {
        "ts": utc_iso(),
        "level": level,
        "event": event,
        **fields,
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()
