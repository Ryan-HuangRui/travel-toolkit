---
name: travel-maps-planner
description: Plan travel itineraries with provider-aware place lookup, route checks, and route matrices. Use when building, comparing, verifying, or refining travel routes, daily logistics, or geographic clusters; supports Google Maps and Amap.
---

# Travel Maps Planner

Use this skill when a travel decision needs normalized places, transport evidence, or route clustering. It supports multiple map providers without treating their identifiers, coverage, coordinate systems, or live traffic as interchangeable.

## Provider choice

1. Prefer the provider that has the best coverage where the traveller will be. Google Maps is the default for global travel; Amap is usually the stronger starting point for mainland-China POI and local routing.
2. Keep every result's `provider`, provider place ID, coordinate system, source timestamp, and cache status. Never compare raw coordinates from two providers without recording their coordinate reference systems.
3. Amap domestic Web Service results use GCJ-02. Its overseas services require separate entitlement and use WGS84; do not silently send one coordinate system to the other.
4. Routing, traffic, public transport, and opening hours are mutable. Mark important legs for travel-day recheck.
5. A provider is evidence, not authority to change the itinerary. Feed accepted place and route facts back to `plan-travel-guide`'s canonical `trip.json` only after user confirmation.

Read [the provider contract](references/provider-contract.md) before adding a provider or combining results. Read [Amap notes](references/amap-web-service.md) for Amap calls and [Google Maps notes](references/google-maps-api.md) when changing Google fields or billing-sensitive behavior.

## Workflow

1. Gather dates, city/region, lodging area, must-visit places, pace, luggage, mobility needs, hard reservations, and preferred transport.
2. Select and state the provider. Normalize a small set of candidate places first; preserve the provider's IDs, display name, address, location, and deep link.
3. Check fragile pairs such as lodging → first stop, last stop → dinner, and station/airport → lodging. Use walk/transit/drive according to the situation.
4. Build a matrix only after pruning candidates. Ask or narrow before evaluating more than 12 places.
5. Return evidence tables, recommended day grouping, backups, and freshness checks. Do not write workspace files unless the user requests persistence.

## Google Maps

Set `GOOGLE_MAPS_API_KEY` in the process environment, or in a private file selected by `TRAVEL_MAPS_ENV_FILE`. Never print or commit a key.

```bash
python3 scripts/places_text_search.py "Louvre Museum Paris" --region-code FR --max-results 3
python3 scripts/route_between.py --origin "Paris Gare de Lyon" --destination "Louvre Museum Paris" --mode TRANSIT --departure-time "2026-09-28T09:00:00+02:00"
```

## Amap

Set `AMAP_API_KEY` in the process environment, or in a private file selected by `AMAP_ENV_FILE`. The bundled Amap scripts default to domestic Web Service endpoints and GCJ-02 coordinates. Use `--international` only with a key entitled for Amap overseas services and WGS84 coordinates.

```bash
python3 scripts/amap_places_text_search.py "故宫博物院" --city 北京 --max-results 3
python3 scripts/amap_route_between.py --origin "116.397128,39.916527" --destination "116.403963,39.915119" --mode WALK
```

For Amap transit, pass city codes explicitly:

```bash
python3 scripts/amap_route_between.py --origin "116.397128,39.916527" --destination "116.403963,39.915119" --mode TRANSIT --origin-city 010 --destination-city 010
```

## Output contract

Travel output should include a decision summary first, then place evidence, route evidence, daily grouping, backups, and unresolved travel-day checks. Include provider and coordinate-system columns whenever locations are shown.

Use `assets/itinerary.zh.md` as the reusable itinerary template.
