#!/usr/bin/env python3
"""Shared Google Maps helpers for the travel-maps-planner skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_ENV_FILE = Path(
    os.environ.get(
        "TRAVEL_MAPS_ENV_FILE",
        Path.home() / ".config" / "codex" / "travel-maps-planner.env",
    )
).expanduser()
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "travel-toolkit" / "google-maps"
API_KEY_ENV = "GOOGLE_MAPS_API_KEY"


class MapsApiError(RuntimeError):
    """Raised when a Google Maps API request fails."""


def load_env_file(path: Path = DEFAULT_ENV_FILE) -> None:
    """Load simple export KEY=VALUE lines without executing shell code."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        os.environ.setdefault(key, value)


def get_api_key() -> str:
    load_env_file()
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        raise MapsApiError(
            f"{API_KEY_ENV} is missing. Source {DEFAULT_ENV_FILE} or set the environment variable."
        )
    return api_key


def cache_root() -> Path:
    return Path(os.environ.get("TRAVEL_MAPS_CACHE_DIR", DEFAULT_CACHE_DIR)).expanduser()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def cache_path(namespace: str, url: str, payload: Any, field_mask: str) -> Path:
    digest = hashlib.sha256(stable_json({"url": url, "payload": payload, "field_mask": field_mask}).encode()).hexdigest()
    return cache_root() / namespace / f"{digest}.json"


def post_json(
    *,
    namespace: str,
    url: str,
    payload: dict[str, Any],
    field_mask: str,
    use_cache: bool = True,
    timeout: int = 30,
) -> dict[str, Any] | list[Any]:
    path = cache_path(namespace, url, payload, field_mask)
    if use_cache and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    api_key = get_api_key()
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": field_mask,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise MapsApiError(format_http_error(exc.code, body)) from exc
    except urllib.error.URLError as exc:
        raise MapsApiError(f"Google Maps API request failed: {exc}") from exc

    try:
        data = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise MapsApiError("Google Maps API returned non-JSON response") from exc

    if use_cache:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{os.getpid()}.{int(time.time())}.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    return data


def format_http_error(status_code: int, body: str) -> str:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return f"Google Maps API HTTP {status_code}: {body[:500]}"
    error = payload.get("error") or {}
    message = error.get("message") or "request failed"
    status = error.get("status")
    reason = None
    service = None
    activation_url = None
    for detail in error.get("details") or []:
        metadata = detail.get("metadata") or {}
        reason = reason or detail.get("reason")
        service = service or metadata.get("serviceTitle") or metadata.get("service")
        activation_url = activation_url or metadata.get("activationUrl")
    parts = [f"Google Maps API HTTP {status_code}"]
    if status:
        parts.append(status)
    if reason:
        parts.append(reason)
    if service:
        parts.append(f"service={service}")
    parts.append(message)
    if activation_url:
        parts.append(f"activation_url={activation_url}")
    return "; ".join(parts)


def parse_lat_lng(value: str) -> dict[str, float] | None:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 2:
        return None
    try:
        lat = float(parts[0])
        lng = float(parts[1])
    except ValueError:
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    return {"latitude": lat, "longitude": lng}


def waypoint(value: str, *, kind: str = "auto") -> dict[str, Any]:
    value = value.strip()
    if not value:
        raise argparse.ArgumentTypeError("waypoint value cannot be empty")

    if kind == "auto":
        lat_lng = parse_lat_lng(value)
        if lat_lng:
            return {"location": {"latLng": lat_lng}}
        if value.startswith("places/"):
            return {"placeId": value.removeprefix("places/")}
        if re.fullmatch(r"[A-Za-z0-9_-]{20,}", value):
            return {"placeId": value}
        return {"address": value}
    if kind == "place-id":
        return {"placeId": value.removeprefix("places/")}
    if kind == "address":
        return {"address": value}
    if kind == "lat-lng":
        lat_lng = parse_lat_lng(value)
        if not lat_lng:
            raise argparse.ArgumentTypeError("lat-lng must be formatted as 'lat,lng'")
        return {"location": {"latLng": lat_lng}}
    raise argparse.ArgumentTypeError(f"unsupported waypoint kind: {kind}")


def duration_seconds(duration: str | None) -> int | None:
    if not duration:
        return None
    match = re.fullmatch(r"(-?\d+(?:\.\d+)?)s", duration)
    if not match:
        return None
    return int(float(match.group(1)))


def print_json(value: Any) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def add_cache_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--no-cache", action="store_true", help="Bypass local cache for this request")
