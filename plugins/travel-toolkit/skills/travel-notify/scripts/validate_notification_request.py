#!/usr/bin/env python3
"""Validate the platform-neutral Travel Notify request contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED = {"schema", "id", "kind", "recipient_profile", "delivery_mode", "state", "authorized", "idempotency_key", "content"}
FORBIDDEN_KEYS = {"chat_id", "open_id", "user_id", "app_secret", "access_token", "tenant_access_token"}
ALIAS = re.compile(r"^[a-z][a-z0-9-]{1,62}$")


def validate(request: dict[str, Any]) -> list[str]:
    errors = [f"missing required field: {field}" for field in sorted(REQUIRED - request.keys())]
    if request.get("schema") != "trip-buddy-notification/v1":
        errors.append("schema must be trip-buddy-notification/v1")
    if not isinstance(request.get("recipient_profile"), str) or not ALIAS.fullmatch(request.get("recipient_profile", "")):
        errors.append("recipient_profile must be a semantic lowercase alias")
    if request.get("delivery_mode") not in {"manual", "scheduled", "alert_only"}:
        errors.append("delivery_mode must be manual, scheduled, or alert_only")
    if request.get("state") not in {"planned", "document_verified", "sending", "notified"}:
        errors.append("state is invalid")
    if not isinstance(request.get("authorized"), bool):
        errors.append("authorized must be boolean")
    if not isinstance(request.get("idempotency_key"), str) or len(request.get("idempotency_key", "")) < 8:
        errors.append("idempotency_key must be a stable nonempty string")
    content = request.get("content")
    if not isinstance(content, dict) or not all(isinstance(content.get(key), str) and content[key].strip() for key in ("title", "body")):
        errors.append("content.title and content.body must be nonempty strings")
    if isinstance(content, dict) and content.get("artifact_url") and not str(content["artifact_url"]).startswith("https://"):
        errors.append("content.artifact_url must use https")

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if key in FORBIDDEN_KEYS:
                    errors.append(f"forbidden private field: {key}")
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    visit(request)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("request", type=Path)
    args = parser.parse_args()
    try:
        request = json.loads(args.request.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"cannot read request JSON: {exc}")
    if not isinstance(request, dict):
        parser.error("request must be a JSON object")
    errors = validate(request)
    if errors:
        parser.error("; ".join(errors))
    print("Notification request is valid!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
