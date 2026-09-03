# Map Provider Contract

Providers are adapters, not a pooled truth source. A normalized place or route must retain the provider's identity and source context.

## Place result

```json
{
  "provider": "google|amap",
  "provider_place_id": "string",
  "display_name": "string",
  "formatted_address": "string",
  "location": {"longitude": 116.397, "latitude": 39.916, "coordinate_system": "GCJ-02"},
  "maps_uri": "https://...",
  "checked_at": "2026-01-01T00:00:00Z"
}
```

## Route result

```json
{
  "provider": "google|amap",
  "mode": "WALK|TRANSIT|DRIVE",
  "origin": {"coordinate_system": "GCJ-02"},
  "destination": {"coordinate_system": "GCJ-02"},
  "duration_seconds": 900,
  "distance_meters": 1200,
  "checked_at": "2026-01-01T00:00:00Z",
  "cached": false
}
```

Do not merge provider IDs. Do not apply coordinate conversion implicitly. A route response is a time-bound observation, not a durable itinerary fact until the traveller accepts it.
