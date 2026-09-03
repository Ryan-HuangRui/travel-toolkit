# Google Maps API Notes

Use these references when patching or extending the bundled scripts:

- Places API (New) Text Search: `https://developers.google.com/maps/documentation/places/web-service/text-search`
- Places Text Search REST method: `https://developers.google.com/maps/documentation/places/web-service/reference/rest/v1/places/searchText`
- Routes API Compute Routes: `https://developers.google.com/maps/documentation/routes/compute_route_directions`
- Routes API `computeRoutes` REST method: `https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRoutes`
- Route Matrix overview: `https://developers.google.com/maps/documentation/routes/compute_route_matrix`
- Route Matrix REST method: `https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRouteMatrix`
- Route field masks: `https://developers.google.com/maps/documentation/routes/choose_fields-rm`

Operational notes:

- Always send `X-Goog-Api-Key` from `GOOGLE_MAPS_API_KEY`; never hard-code keys.
- Always send `X-Goog-FieldMask`; Routes API methods fail without it.
- Prefer `place_id` waypoints after resolving places. Addresses are acceptable for quick tests but less stable.
- Cache route and place responses locally because itinerary work repeats the same calls.
- Public transit availability and route details vary by region and date. Mark itinerary outputs as requiring same-day verification.
- Route Matrix cost grows as `origins x destinations`; cap candidate places before calling it.
