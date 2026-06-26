from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FORBIDDEN_AUDIT_KEYS = {
    "access_token",
    "refresh_token",
    "subjectToken",
    "subject_token",
    "password",
    "otp",
    "recovery_code",
    "client_secret",
    "private_key",
    "session_id",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class AuditWriter:
    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        clean_event = self._clean_event(event)
        clean_event.setdefault("eventId", f"evt_{uuid.uuid4().hex}")
        clean_event.setdefault("occurredAt", utc_now())
        line = json.dumps(clean_event, sort_keys=True, separators=(",", ":"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(line)
                handle.write("\n")
        return clean_event

    def read_events(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped:
                    events.append(json.loads(stripped))
        return events

    def _clean_event(self, event: dict[str, Any]) -> dict[str, Any]:
        clean: dict[str, Any] = {}
        for key, value in event.items():
            if key in FORBIDDEN_AUDIT_KEYS:
                continue
            if isinstance(value, dict):
                clean[key] = self._clean_event(value)
            else:
                clean[key] = value
        return clean


def build_event(
    *,
    operation: str,
    target_type: str,
    target_id: str,
    outcome: str,
    correlation_id: str,
    actor_type: str,
    reason_code: str | None = None,
    actor_account_id: str | None = None,
    client_id: str | None = None,
    keycloak_event_ref: str | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "actorType": actor_type,
        "operation": operation,
        "targetType": target_type,
        "targetId": target_id,
        "outcome": outcome,
        "correlationId": correlation_id,
    }
    if reason_code:
        event["reasonCode"] = reason_code
    if actor_account_id:
        event["actorAccountId"] = actor_account_id
    if client_id:
        event["clientId"] = client_id
    if keycloak_event_ref:
        event["keycloakEventRef"] = keycloak_event_ref
    return event

