#!/usr/bin/env python3
"""Search places with Google Places API (New) Text Search."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from typing import Any

from maps_common import MapsApiError, add_cache_args, post_json, print_json


URL = "https://places.googleapis.com/v1/places:searchText"
DEFAULT_FIELD_MASK = ",".join(
    [
        "places.id",
        "places.name",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.googleMapsUri",
        "places.rating",
        "places.userRatingCount",
        "places.businessStatus",
        "places.types",
        "places.currentOpeningHours",
    ]
)


def simplify_place(place: dict[str, Any]) -> dict[str, Any]:
    display = place.get("displayName") or {}
    location = place.get("location") or {}
    return {
        "provider": "google",
        "provider_place_id": place.get("id") or (place.get("name") or "").removeprefix("places/"),
        "resource_name": place.get("name"),
        "display_name": display.get("text"),
        "language_code": display.get("languageCode"),
        "formatted_address": place.get("formattedAddress"),
        "maps_uri": place.get("googleMapsUri"),
        "location": {
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "coordinate_system": "WGS84",
        }
        if location
        else None,
        "rating": place.get("rating"),
        "user_rating_count": place.get("userRatingCount"),
        "business_status": place.get("businessStatus"),
        "types": place.get("types"),
        "current_opening_hours": place.get("currentOpeningHours"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Text query, for example 'Louvre Museum Paris'")
    parser.add_argument("--language-code", default="zh-CN")
    parser.add_argument("--region-code", default=None)
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--field-mask", default=DEFAULT_FIELD_MASK)
    parser.add_argument("--raw", action="store_true", help="Print raw Google response")
    add_cache_args(parser)
    args = parser.parse_args()

    payload: dict[str, Any] = {
        "textQuery": args.query,
        "languageCode": args.language_code,
        "maxResultCount": args.max_results,
    }
    if args.region_code:
        payload["regionCode"] = args.region_code

    try:
        data = post_json(
            namespace="places",
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

    places = [simplify_place(place) for place in data.get("places", [])]
    print_json({"provider": "google", "coordinate_system": "WGS84", "query": args.query, "checked_at": datetime.now(UTC).isoformat(), "places": places})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
