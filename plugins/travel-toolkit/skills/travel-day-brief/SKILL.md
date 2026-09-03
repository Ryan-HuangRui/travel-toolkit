---
name: travel-day-brief
description: Prepare a practical, dated morning travel brief from the current itinerary day plus fresh local conditions. Use for Trip Buddy in-trip daily briefs covering schedule, weather, clothing, access, and contingencies; not for evergreen culture content or unverified alerts.
---

# Travel Day Brief

Read [the daily-brief contract](references/daily-brief-contract.md) before preparing the brief.

1. Resolve the current calendar day in the destination timezone and read only that day's confirmed/accepted itinerary records.
2. Refresh mutable conditions: local forecast, official weather warnings, transport/venue status, and any booking-specific requirement. Cite direct sources and record `checked_at` and `valid_until`.
3. Lead with what changes the day: fixed times, weather-sensitive choices, clothing/gear implications, access friction, and one fallback. Do not rewrite the entire trip plan.
4. Escalate an issue to `travel-disruption-watch` only when it meets the alert threshold. Otherwise leave it in the daily brief.
5. Return a dated local source with expiration at local day end. Do not send a message or modify itinerary facts.
