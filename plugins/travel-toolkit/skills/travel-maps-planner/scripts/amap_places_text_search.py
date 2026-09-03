#!/usr/bin/env python3
"""Search Amap places and emit provider-preserving normalized records."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime

from amap_common import AmapApiError, emit, get_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--city")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--international", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.max_results <= 50:
        parser.error("--max-results must be between 1 and 50")
    try:
        payload = get_json("/v3/place/text", {"keywords": args.query, "city": args.city, "citylimit": "true" if args.city else None, "offset": args.max_results, "extensions": "base"}, international=args.international)
    except AmapApiError as exc:
        parser.error(str(exc))
    coordinate_system = "WGS84" if args.international else "GCJ-02"
    now = datetime.now(UTC).isoformat()
    places = []
    for poi in payload.get("pois", []):
        try:
            longitude, latitude = (float(item) for item in poi.get("location", "").split(",", 1))
        except ValueError:
            continue
        places.append({"provider": "amap", "provider_place_id": poi.get("id"), "display_name": poi.get("name"), "formatted_address": poi.get("address"), "location": {"longitude": longitude, "latitude": latitude, "coordinate_system": coordinate_system}, "maps_uri": f"https://uri.amap.com/marker?position={poi.get('location')}&name={poi.get('name', '')}", "checked_at": now})
    emit({"provider": "amap", "coordinate_system": coordinate_system, "checked_at": now, "places": places})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
