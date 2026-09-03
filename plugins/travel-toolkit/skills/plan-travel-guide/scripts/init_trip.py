#!/usr/bin/env python3
"""Initialize a portable Travel Plan Bundle without overwriting existing data."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path


def iso_date(value: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid ISO date: {value}") from exc
    return value


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "travel-plan"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--trip-id")
    parser.add_argument("--start-date", required=True, type=iso_date)
    parser.add_argument("--end-date", required=True, type=iso_date)
    parser.add_argument("--planning-phase", choices=("exploration", "detailed"), default="exploration")
    parser.add_argument("--date-flexibility", choices=("fixed", "tentative", "unknown"), default="unknown")
    parser.add_argument("--discovery-days-before", type=int)
    parser.add_argument("--discovery-days-after", type=int)
    parser.add_argument("--timezone", default="UTC")
    parser.add_argument("--language", default="en")
    parser.add_argument("--currency", default="USD")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    start = date.fromisoformat(args.start_date)
    end = date.fromisoformat(args.end_date)
    if end < start:
        print("error: end date is before start date", file=sys.stderr)
        return 2

    default_discovery_days = 0 if args.date_flexibility == "fixed" else 3
    discovery_days_before = args.discovery_days_before if args.discovery_days_before is not None else default_discovery_days
    discovery_days_after = args.discovery_days_after if args.discovery_days_after is not None else default_discovery_days
    if discovery_days_before < 0 or discovery_days_after < 0:
        print("error: discovery days must be non-negative integers", file=sys.stderr)
        return 2

    currency = args.currency.upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        print("error: currency must be a three-letter code", file=sys.stderr)
        return 2

    output_dir = args.output_dir.resolve()
    trip_path = output_dir / "trip.json"
    if trip_path.exists():
        print(f"error: refusing to overwrite existing {trip_path}", file=sys.stderr)
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    trip = {
        "schema_version": "1.0",
        "revision": 0,
        "updated_at": now,
        "trip": {
            "id": args.trip_id or slugify(args.title),
            "title": args.title,
            "planning_phase": args.planning_phase,
            "start_date": args.start_date,
            "end_date": args.end_date,
            "date_flexibility": {
                "status": args.date_flexibility,
                "days_before": discovery_days_before,
                "days_after": discovery_days_after,
            },
            "timezone": args.timezone,
            "language": args.language,
            "currency": currency,
        },
        "constraints": [],
        "places": [],
        "decisions": [],
        "days": [],
        "reservations": [],
        "candidates": [],
        "tasks": [],
        "budget": [],
        "sources": [],
    }
    trip_path.write_text(json.dumps(trip, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    script_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(script_dir))
    from render_trip import render_bundle  # pylint: disable=import-outside-toplevel

    render_bundle(trip_path)
    print(f"Created Travel Plan Bundle: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
