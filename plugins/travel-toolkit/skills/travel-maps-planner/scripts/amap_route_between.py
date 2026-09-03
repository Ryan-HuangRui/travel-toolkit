#!/usr/bin/env python3
"""Get one Amap walking, transit, or driving route between two coordinates."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime

from amap_common import AmapApiError, coordinate, emit, get_json


PATHS = {"WALK": "/v5/direction/walking", "DRIVE": "/v5/direction/driving", "TRANSIT": "/v5/direction/transit/integrated"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--mode", choices=PATHS, required=True)
    parser.add_argument("--origin-city")
    parser.add_argument("--destination-city")
    parser.add_argument("--international", action="store_true")
    args = parser.parse_args()
    if args.mode == "TRANSIT" and not (args.origin_city and args.destination_city):
        parser.error("Amap transit requires --origin-city and --destination-city city codes")
    try:
        origin = coordinate(args.origin)
        destination = coordinate(args.destination)
        payload = get_json(PATHS[args.mode], {"origin": f"{origin[0]},{origin[1]}", "destination": f"{destination[0]},{destination[1]}", "city1": args.origin_city, "city2": args.destination_city, "strategy": 32 if args.mode == "DRIVE" else None}, international=args.international)
    except AmapApiError as exc:
        parser.error(str(exc))
    route = payload.get("route", {})
    candidates = (route.get("transits") if args.mode == "TRANSIT" else route.get("paths")) or []
    first = candidates[0] if candidates else {}
    coordinate_system = "WGS84" if args.international else "GCJ-02"
    emit({"provider": "amap", "mode": args.mode, "origin": {"longitude": origin[0], "latitude": origin[1], "coordinate_system": coordinate_system}, "destination": {"longitude": destination[0], "latitude": destination[1], "coordinate_system": coordinate_system}, "distance_meters": int(first["distance"]) if str(first.get("distance", "")).isdigit() else None, "duration_seconds": int(first["duration"]) if str(first.get("duration", "")).isdigit() else None, "checked_at": datetime.now(UTC).isoformat(), "raw_route_count": len(candidates)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
