#!/usr/bin/env python3
"""Small, dependency-free helpers for Amap Web Service adapters."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


class AmapApiError(RuntimeError):
    pass


def load_env_file() -> None:
    path = Path(os.environ.get("AMAP_ENV_FILE", "~/.config/travel-toolkit/amap.env")).expanduser()
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip().removeprefix("export ").strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key.strip()):
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def api_key() -> str:
    load_env_file()
    key = os.environ.get("AMAP_API_KEY")
    if not key:
        raise AmapApiError("AMAP_API_KEY is missing. Set it or configure AMAP_ENV_FILE.")
    return key


def endpoint(path: str, *, international: bool) -> str:
    host = "sg-restapi.opnavi.com" if international else "restapi.amap.com"
    return f"https://{host}{path}"


def get_json(path: str, params: dict[str, Any], *, international: bool) -> dict[str, Any]:
    query = {key: str(value) for key, value in params.items() if value not in (None, "")}
    query["key"] = api_key()
    request = urllib.request.Request(f"{endpoint(path, international=international)}?{urllib.parse.urlencode(query)}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise AmapApiError(f"Amap HTTP {exc.code}") from exc
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise AmapApiError(f"Amap request failed: {exc}") from exc
    if str(payload.get("status")) != "1":
        raise AmapApiError(f"Amap request failed: {payload.get('info', 'unknown error')} ({payload.get('infocode', 'unknown')})")
    return payload


def coordinate(value: str) -> tuple[float, float]:
    try:
        longitude, latitude = (float(part.strip()) for part in value.split(",", 1))
    except ValueError as exc:
        raise AmapApiError("coordinates must be longitude,latitude") from exc
    if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
        raise AmapApiError("coordinates are outside valid longitude/latitude bounds")
    return longitude, latitude


def emit(value: dict[str, Any]) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
