# Travel Plan Bundle Contract

Read this file before creating or structurally editing a Travel Plan Bundle.

## Contents

- [Contract](#contract)
- [Top-level fields](#top-level-fields)
- [Trip identity](#trip-identity)
- [Planning phases](#planning-phases)
- [City stay windows](#city-stay-windows)
- [Stable IDs and references](#stable-ids-and-references)
- [Execution and decision states](#execution-and-decision-states)
- [Destination discoveries](#destination-discoveries)
- [Freshness and provenance](#freshness-and-provenance)
- [Day items](#day-items)
- [Reservations and private data](#reservations-and-private-data)
- [Derived views](#derived-views)
- [Workspace integration](#workspace-integration)

## Contract

`trip.json` is the only canonical plan. `itinerary.md`, `planning.md`, `budget.csv`, and `sources.md` are generated views and must not be maintained as independent facts.

Every bundle uses this layout:

```text
<trip-id>/
├── trip.json
├── itinerary.md
├── planning.md
├── budget.csv
└── sources.md
```

Additional exports belong under `exports/`. Private operational data does not belong in the standard bundle.

## Top-level fields

| Field | Required | Meaning |
|---|---:|---|
| `schema_version` | yes | Artifact contract version, currently `1.0` |
| `revision` | yes | Monotonically increasing plan revision |
| `updated_at` | yes | ISO 8601 timestamp for the canonical data |
| `trip` | yes | Trip identity, dates, time zone, language, and currency |
| `constraints` | yes | Hard and soft planning constraints |
| `places` | yes | Normalized place registry |
| `decisions` | yes | Proposed, accepted, rejected, or superseded choices |
| `days` | yes | Daily itinerary and scheduled items |
| `reservations` | yes | Lodging, transport, ticket, meal, and activity reservations |
| `candidates` | yes | Options and destination discoveries still being evaluated |
| `tasks` | yes | Actionable planning and booking work |
| `budget` | yes | Estimated, quoted, paid, refunded, or cancelled costs |
| `sources` | yes | Evidence and freshness metadata |

## Trip identity

`trip` requires:

```json
{
  "id": "sample-trip-2026",
  "title": "France Trip 2026",
  "planning_phase": "exploration",
  "start_date": "2026-09-27",
  "end_date": "2026-10-07",
  "date_flexibility": {
    "status": "tentative",
    "days_before": 3,
    "days_after": 3
  },
  "timezone": "Europe/Paris",
  "language": "zh-CN",
  "currency": "EUR"
}
```

Use `planning_phase: exploration` while the skeleton is open and `planning_phase: detailed` only after explicit user acceptance. Use ISO dates. `start_date` and `end_date` are the current working plan even when tentative. `date_flexibility` controls the nearby-date discovery window; it does not authorize changing the canonical dates. Allowed statuses are `fixed`, `tentative`, and `unknown`. Use the user's tolerance, or three days before and after when dates are tentative or unknown and no tolerance was provided. Use an IANA time-zone name when known. Keep personal traveler names out unless they are operationally necessary and the user explicitly requests persistence.

## Planning phases

Use `exploration` while the trip skeleton is under discussion. It is valid for `days` to be empty, city `stay_window` records to be `unassigned`, and route or skeleton options to remain candidates. Research should focus on decisions that can change the route, dates, nights, or destination set.

Move to `detailed` only after the user explicitly accepts the skeleton. Record the accepted decisions, update relevant city windows, and then build daily items, transport, lodging, reservations, tasks, and budget detail. Do not infer phase acceptance from silence or from the existence of a recommended option.

## City stay windows

City dates may remain undecided while destination discovery is underway. Store an optional `stay_window` on a city place:

```json
{
  "id": "place-paris",
  "name": "Paris",
  "stay_window": {
    "status": "tentative",
    "start_date": "2026-10-02",
    "end_date": "2026-10-05",
    "days_before": 2,
    "days_after": 2
  }
}
```

Allowed statuses are `fixed`, `tentative`, and `unassigned`. A fixed window has dates and zero flexibility. A tentative window has working dates and optional nearby-date tolerance. An unassigned window intentionally omits dates; search the overall trip window and allow a standout event to propose the city placement. Do not invent city dates merely to satisfy the structure.

## Stable IDs and references

Use lowercase IDs containing letters, numbers, `_`, or `-`. Preserve an existing ID when editing the associated record.

References use IDs:

- day items and reservations reference `place_id`;
- verified records reference `source_ids`;
- tasks use `related_ids` for itinerary items, reservations, candidates, or decisions.

Do not use display names as relational keys.

## Execution and decision states

Use these day-item and reservation states:

- `proposed`
- `confirmed`
- `booked`
- `completed`
- `cancelled`

Use these decision states:

- `proposed`
- `accepted`
- `rejected`
- `superseded`

Use these candidate states:

- `shortlisted`
- `recommended`
- `selected`
- `rejected`

Use these task states:

- `todo`
- `doing`
- `waiting`
- `blocked`
- `done`
- `dropped`

Use these budget states:

- `estimated`
- `quoted`
- `paid`
- `refunded`
- `cancelled`

## Destination discoveries

Represent date-matched events, seasonal experiences, and distinctive local character as candidates until the user accepts them and they pass the feasibility gate.

Use discovery categories such as:

- `local_event`
- `festival`
- `performance`
- `exhibition`
- `sports`
- `market`
- `seasonal_experience`
- `local_specialty`
- `food_and_drink`
- `neighborhood_experience`

Recommended discovery fields are:

```json
{
  "id": "candidate-harvest-festival",
  "category": "festival",
  "title": "Regional harvest festival",
  "status": "recommended",
  "start_date": "2026-10-03",
  "end_date": "2026-10-04",
  "start_time": "17:00",
  "end_time": "22:00",
  "place_id": "place-old-town",
  "date_fit": "within_city_window",
  "date_confidence": "confirmed",
  "route_fit": "nearby",
  "booking_timing": "walk_in",
  "notes": "Fits the evening after the old-town route.",
  "source_ids": ["src-festival-official"]
}
```

Allowed `date_confidence` values are `confirmed`, `expected`, and `unknown`. Allowed `route_fit` values are `direct`, `nearby`, `detour`, `conflict`, and `unknown`. Allowed `booking_timing` values are `book_early`, `monitor`, `walk_in`, and `not_applicable`.

Allowed `date_fit` values are `within_city_window`, `overlaps_city_window`, `within_trip_unassigned`, `nearby_before`, `nearby_after`, and `seasonal_flexible`. `within_trip_unassigned` means the city has no dates yet and the event could anchor its placement. Nearby values fall inside the permitted city or trip discovery window and require a user decision before changing dates.

For an event that can anchor an unassigned city, use `date_fit: within_trip_unassigned` and a `date_adjustment` with `scope: city_stay`, `kind: place_city_stay`, proposed city dates, and `minimum_change_days: 0`. This proposes city placement without changing the overall trip window.

Represent a worthwhile nearby-date option like this:

```json
{
  "id": "candidate-lantern-festival",
  "category": "festival",
  "title": "Old-town lantern festival",
  "status": "recommended",
  "start_date": "2026-10-10",
  "end_date": "2026-10-10",
  "place_id": "place-old-town",
  "date_fit": "nearby_after",
  "date_confidence": "confirmed",
  "route_fit": "direct",
  "booking_timing": "monitor",
  "date_adjustment": {
    "scope": "city_stay",
    "kind": "move_city_stay",
    "proposed_start_date": "2026-10-08",
    "proposed_end_date": "2026-10-10",
    "minimum_change_days": 3,
    "affected_ids": ["reservation-old-town-hotel"],
    "impact_summary": "Moves the final city stay three days later; hotel and outbound train need repricing.",
    "decision_prompt": "Do you want to move the old-town stay to include this festival?"
  },
  "source_ids": ["src-lantern-festival-official"]
}
```

Allowed adjustment scopes are `trip` and `city_stay`. Allowed kinds are `shift`, `extend_start`, `extend_end`, `place_city_stay`, `move_city_stay`, and `reorder_route`. Use `place_city_stay` to assign a previously unassigned city around an event without changing the overall trip dates. `minimum_change_days` is the smallest number of already assigned calendar days that must change and can be zero for a new placement.

Never write proposed dates into `trip.start_date`, `trip.end_date`, or `days[]` until the user accepts the change. While pending, render the proposal and impact separately. After acceptance, update affected dates and anchors, record the decision, increment the revision, validate, and render again.

Do not use `confirmed` date confidence for an annual event until the current year's dates are published. A discovery can be `recommended` while its date confidence remains `expected`; keep these concepts separate.

## Freshness and provenance

Each source has:

```json
{
  "id": "src-notre-dame-hours",
  "type": "official_site",
  "title": "Notre-Dame opening hours",
  "url": "https://example.com",
  "checked_at": "2026-07-22T10:00:00Z",
  "freshness": "current",
  "notes": "Recheck shortly before travel."
}
```

Allowed source types:

- `user_statement`
- `official_site`
- `map`
- `booking_platform`
- `email`
- `calendar`
- `document`
- `estimate`
- `other`

Allowed freshness values:

- `current`
- `needs_refresh`
- `unknown`

Freshness describes the evidence, not whether the user accepted a plan.

## Day items

Each `days[]` record contains a date, optional base place, summary, and items. Day items may contain:

```json
{
  "id": "day-01-notre-dame",
  "type": "visit",
  "title": "Notre-Dame light visit",
  "start_time": "14:30",
  "end_time": "15:15",
  "place_id": "place-notre-dame",
  "status": "confirmed",
  "notes": "Enter only if the queue is reasonable.",
  "fallback": "Exterior, square, and riverbank.",
  "source_ids": ["src-notre-dame-hours"]
}
```

Allowed item types are `visit`, `meal`, `transfer`, `checkin`, `checkout`, `event`, `rest`, `free_time`, and `other`.

Use local `HH:MM` times. Keep items ordered by start time when times are known. Do not invent precision for uncertain activities.

## Reservations and private data

Record only operationally useful, share-safe fields: category, title, dates, general location, status, cancellation deadline, quoted/paid amount, and source references.

Do not put complete confirmation codes, payment details, host contact data, passport data, or unnecessarily precise private-home addresses in `trip.json`.

## Derived views

`render_trip.py` generates:

- `itinerary.md`: readable trip skeleton and daily plan;
- `planning.md`: constraints, decisions, candidates, reservations, and tasks;
- `budget.csv`: spreadsheet-friendly costs;
- `sources.md`: evidence, checked time, freshness, and notes.

Each Markdown view records the source revision. Regenerate the entire set after every canonical update.

## Workspace integration

A repository may store the bundle inside its own project directory or summarize confirmed changes elsewhere. That integration is outside this contract.

An adapter must:

- consume `trip.json` rather than scrape generated Markdown;
- respect `schema_version`;
- avoid duplicating the complete itinerary as another maintained truth;
- perform external writes only with user authorization.
