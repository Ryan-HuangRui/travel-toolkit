---
name: travel-disruption-watch
description: Assess a possible weather, transport, venue, safety, or operational disruption against a specific trip date and place. Use for Trip Buddy event monitoring or suspected travel impacts; do not alert from generic news, social posts, or forecasts unrelated to the itinerary.
---

# Travel Disruption Watch

Read [the alert contract](references/alert-contract.md) before classifying an event.

1. Resolve the affected place, local date/time, and itinerary reference first.
2. Verify against an official venue, carrier, public authority, weather service, or another direct primary source. Do not infer an impact from headlines, social posts, or a different city/date.
3. Classify `no_action`, `daily_brief`, or `alert`. An alert needs a material, concrete effect and a workable fallback.
4. Record source URL, `checked_at`, `valid_until`, confidence, impact, and fallback. Recheck before any alert is delivered.
5. Return an assessment to Trip Buddy; do not write to the itinerary, create a group message, or amplify uncertain claims.
