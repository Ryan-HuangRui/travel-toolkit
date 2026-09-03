#!/usr/bin/env python3
"""Compute a route-duration matrix for candidate travel places."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from maps_common import MapsApiError, add_cache_args, duration_seconds, post_json, print_json, waypoint


URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
DEFAULT_FIELD_MASK = "originIndex,destinationIndex,duration,distanceMeters,status,condition"
TRAVEL_MODES = ("DRIVE", "WALK", "BICYCLE", "TRANSIT", "TWO_WHEELER")


def place_waypoint(place: dict[str, Any]) -> dict[str, Any]:
    place_id = place.get("place_id") or place.get("placeId") or place.get("id")
    if place_id:
        return {"waypoint": waypoint(str(place_id), kind="place-id")}
    address = place.get("formatted_address") or place.get("formattedAddress") or place.get("address")
    if address:
        return {"waypoint": waypoint(str(address), kind="address")}
    location = place.get("location") or {}
    lat = location.get("latitude") or location.get("lat")
    lng = location.get("longitude") or location.get("lng")
    if lat is not None and lng is not None:
        return {"waypoint": waypoint(f"{lat},{lng}", kind="lat-lng")}
    raise ValueError(f"place is missing place_id, address, and location: {place!r}")


def place_label(place: dict[str, Any], index: int) -> str:
    return (
        place.get("display_name")
        or place.get("displayName")
        or place.get("name")
        or place.get("formatted_address")
        or place.get("address")
        or f"place-{index}"
    )


def load_places(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "places" in data:
        data = data["places"]
    if not isinstance(data, list):
        raise ValueError("places file must be a JSON list or an object with a places list")
    return data


def simplify_element(element: dict[str, Any], labels: list[str]) -> dict[str, Any]:
    origin_index = element.get("originIndex")
    destination_index = element.get("destinationIndex")
    duration = element.get("duration")
    distance_meters = element.get("distanceMeters")
    return {
        "origin_index": origin_index,
        "destination_index": destination_index,
        "origin": labels[origin_index] if isinstance(origin_index, int) and origin_index < len(labels) else None,
        "destination": labels[destination_index]
        if isinstance(destination_index, int) and destination_index < len(labels)
        else None,
        "duration": duration,
        "duration_seconds": duration_seconds(duration),
        "distance_meters": distance_meters,
        "distance_km": round(distance_meters / 1000, 2) if isinstance(distance_meters, int) else None,
        "status": element.get("status"),
        "condition": element.get("condition"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--places", required=True, type=Path, help="JSON from places_text_search.py or a list of places")
    parser.add_argument("--mode", choices=TRAVEL_MODES, default="TRANSIT")
    parser.add_argument("--departure-time", help="RFC3339 timestamp")
    parser.add_argument("--language-code", default="zh-CN")
    parser.add_argument("--max-places", type=int, default=12, help="Safety cap; matrix cost grows as N x N")
    parser.add_argument("--field-mask", default=DEFAULT_FIELD_MASK)
    parser.add_argument("--raw", action="store_true")
    add_cache_args(parser)
    args = parser.parse_args()

    places = load_places(args.places)
    if len(places) > args.max_places:
        raise SystemExit(f"Refusing to compute {len(places)} x {len(places)} matrix; use --max-places to override")

    labels = [place_label(place, index) for index, place in enumerate(places)]
    route_places = [place_waypoint(place) for place in places]
    payload: dict[str, Any] = {
        "origins": route_places,
        "destinations": route_places,
        "travelMode": args.mode,
        "languageCode": args.language_code,
        "units": "METRIC",
    }
    if args.departure_time:
        payload["departureTime"] = args.departure_time

    try:
        data = post_json(
            namespace="matrices",
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

    elements = [simplify_element(element, labels) for element in data]
    print_json({"mode": args.mode, "place_count": len(places), "places": labels, "elements": elements})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
