#!/usr/bin/env python3
"""Compute a route between two places with Google Routes API."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from typing import Any

from maps_common import MapsApiError, add_cache_args, duration_seconds, post_json, print_json, waypoint


URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
DEFAULT_FIELD_MASK = ",".join(
    [
        "routes.duration",
        "routes.distanceMeters",
        "routes.description",
        "routes.localizedValues",
        "routes.routeLabels",
        "routes.legs.localizedValues",
        "routes.legs.steps.travelMode",
        "routes.legs.steps.localizedValues",
        "routes.legs.steps.transitDetails",
    ]
)
TRAVEL_MODES = ("DRIVE", "WALK", "BICYCLE", "TRANSIT", "TWO_WHEELER")


def summarize_route(route: dict[str, Any]) -> dict[str, Any]:
    duration = route.get("duration")
    distance_meters = route.get("distanceMeters")
    legs = route.get("legs") or []
    steps_summary: list[dict[str, Any]] = []
    for leg in legs:
        for step in leg.get("steps") or []:
            localized = step.get("localizedValues") or {}
            transit = step.get("transitDetails") or {}
            line = transit.get("transitLine") or {}
            vehicle = line.get("vehicle") or {}
            steps_summary.append(
                {
                    "travel_mode": step.get("travelMode"),
                    "duration_text": (localized.get("staticDuration") or {}).get("text"),
                    "distance_text": (localized.get("distance") or {}).get("text"),
                    "transit_line": line.get("name") or line.get("nameShort"),
                    "vehicle_type": vehicle.get("type"),
                    "departure_stop": ((transit.get("stopDetails") or {}).get("departureStop") or {}).get("name"),
                    "arrival_stop": ((transit.get("stopDetails") or {}).get("arrivalStop") or {}).get("name"),
                }
            )
    return {
        "duration": duration,
        "duration_seconds": duration_seconds(duration),
        "distance_meters": distance_meters,
        "distance_km": round(distance_meters / 1000, 2) if isinstance(distance_meters, int) else None,
        "duration_text": ((route.get("localizedValues") or {}).get("duration") or {}).get("text"),
        "static_duration_text": ((route.get("localizedValues") or {}).get("staticDuration") or {}).get("text"),
        "distance_text": ((route.get("localizedValues") or {}).get("distance") or {}).get("text"),
        "description": route.get("description"),
        "route_labels": route.get("routeLabels"),
        "steps": steps_summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True, help="Address, place id, or 'lat,lng'")
    parser.add_argument("--destination", required=True, help="Address, place id, or 'lat,lng'")
    parser.add_argument("--origin-kind", choices=("auto", "address", "place-id", "lat-lng"), default="auto")
    parser.add_argument("--destination-kind", choices=("auto", "address", "place-id", "lat-lng"), default="auto")
    parser.add_argument("--mode", choices=TRAVEL_MODES, default="TRANSIT")
    parser.add_argument("--departure-time", help="RFC3339 timestamp, for example 2026-09-28T09:00:00+02:00")
    parser.add_argument("--arrival-time", help="RFC3339 timestamp. Do not combine with --departure-time.")
    parser.add_argument("--language-code", default="zh-CN")
    parser.add_argument("--region-code")
    parser.add_argument("--alternatives", action="store_true")
    parser.add_argument("--field-mask", default=DEFAULT_FIELD_MASK)
    parser.add_argument("--raw", action="store_true")
    add_cache_args(parser)
    args = parser.parse_args()

    if args.departure_time and args.arrival_time:
        parser.error("--departure-time and --arrival-time are mutually exclusive")

    payload: dict[str, Any] = {
        "origin": waypoint(args.origin, kind=args.origin_kind),
        "destination": waypoint(args.destination, kind=args.destination_kind),
        "travelMode": args.mode,
        "languageCode": args.language_code,
        "units": "METRIC",
        "computeAlternativeRoutes": args.alternatives,
    }
    if args.region_code:
        payload["regionCode"] = args.region_code
    if args.departure_time:
        payload["departureTime"] = args.departure_time
    if args.arrival_time:
        payload["arrivalTime"] = args.arrival_time

    try:
        data = post_json(
            namespace="routes",
            url=URL,
            payload=payload,
            field_mask=args.field_mask,
            use_cache=not args.no_cache,
        )
    except MapsApiError as exc:
        print_json({"ok": False, "error": str(exc)})
        return 1
    if args.raw:
        print_json(data)
        return 0

    routes = [summarize_route(route) for route in data.get("routes", [])]
    print_json(
        {
            "provider": "google",
            "coordinate_system": "WGS84",
            "origin": args.origin,
            "destination": args.destination,
            "mode": args.mode,
            "departure_time": args.departure_time,
            "arrival_time": args.arrival_time,
            "route_count": len(routes),
            "checked_at": datetime.now(UTC).isoformat(),
            "routes": routes,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
