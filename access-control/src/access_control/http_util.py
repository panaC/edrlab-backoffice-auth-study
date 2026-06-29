from __future__ import annotations

import json
import re
import uuid
from http.server import BaseHTTPRequestHandler
from typing import Any


CORRELATION_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")


class JsonBodyValidationError(ValueError):
    pass


def correlation_id(value: str | None) -> str:
    if value and CORRELATION_RE.match(value):
        return value
    return f"corr_{uuid.uuid4().hex}"


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    body = handler.rfile.read(length)
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise JsonBodyValidationError("Request body must be a JSON object.")
    return payload


def json_response(
    handler: BaseHTTPRequestHandler,
    status: int,
    body: dict[str, Any] | list[Any],
    corr: str,
    content_type: str = "application/json",
) -> None:
    payload = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(payload)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Correlation-Id", corr)
    handler.end_headers()
    handler.wfile.write(payload)


def problem_response(
    handler: BaseHTTPRequestHandler,
    status: int,
    code: str,
    title: str,
    detail: str,
    corr: str,
) -> None:
    json_response(
        handler,
        status,
        {
            "type": f"https://docs.access-control.example/problems/{code}",
            "title": title,
            "status": status,
            "detail": detail,
            "code": code,
            "correlationId": corr,
            "instance": handler.path,
        },
        corr,
        "application/problem+json",
    )

