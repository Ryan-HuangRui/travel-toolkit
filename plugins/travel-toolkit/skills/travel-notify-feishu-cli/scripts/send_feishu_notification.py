#!/usr/bin/env python3
"""Dry-run by default; send a verified Travel Notify request through lark-cli."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object")
    return payload


def validate_request(request: dict[str, Any]) -> list[str]:
    required = {"schema", "recipient_profile", "state", "authorized", "idempotency_key", "content"}
    errors = [f"missing {field}" for field in sorted(required - request.keys())]
    if request.get("schema") != "trip-buddy-notification/v1":
        errors.append("unsupported request schema")
    if request.get("state") != "sending":
        errors.append("adapter only accepts state=sending")
    if request.get("authorized") is not True:
        errors.append("request is not explicitly authorized")
    content = request.get("content")
    if not isinstance(content, dict) or not isinstance(content.get("title"), str) or not isinstance(content.get("body"), str):
        errors.append("content title and body are required")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--profiles", type=Path, default=Path(os.environ.get("TRAVEL_NOTIFY_PROFILES", "~/.config/travel-toolkit/notifications.json")).expanduser())
    parser.add_argument("--send", action="store_true", help="Perform the visible send after validation")
    args = parser.parse_args()
    try:
        request = load_json(args.request)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"cannot load request: {exc}")
    errors = validate_request(request)
    if errors:
        parser.error("; ".join(errors))
    if not args.send:
        print(json.dumps({"ok": True, "dry_run": True, "recipient_profile": request["recipient_profile"], "idempotency_key": request["idempotency_key"]}, ensure_ascii=False))
        return 0
    try:
        profiles = load_json(args.profiles).get("profiles", {})
        profile = profiles.get(request["recipient_profile"], {})
        if profile.get("channel") != "feishu-cli" or profile.get("identity") != "bot" or not isinstance(profile.get("chat_id"), str):
            raise ValueError("recipient profile must be a Feishu bot profile with a chat_id")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"cannot resolve private recipient profile: {exc}")
    content = request["content"]
    message = f"{content['title']}\n{content['body']}"
    if content.get("artifact_url"):
        message += f"\n{content['artifact_url']}"
    command = ["lark-cli", "im", "+messages-send", "--as", "bot", "--chat-id", profile["chat_id"], "--text", message, "--idempotency-key", request["idempotency_key"]]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(json.dumps({"ok": False, "status": "uncertain", "reason": "lark-cli returned a nonzero exit status"}, ensure_ascii=False), file=sys.stderr)
        return result.returncode
    try:
        receipt = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(json.dumps({"ok": False, "status": "uncertain", "reason": "lark-cli receipt was not JSON"}, ensure_ascii=False), file=sys.stderr)
        return 2
    if receipt.get("ok") is not True:
        print(json.dumps({"ok": False, "status": "uncertain", "reason": "lark-cli did not confirm success"}, ensure_ascii=False), file=sys.stderr)
        return 3
    print(json.dumps({"ok": True, "status": "notified", "recipient_profile": request["recipient_profile"], "idempotency_key": request["idempotency_key"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
