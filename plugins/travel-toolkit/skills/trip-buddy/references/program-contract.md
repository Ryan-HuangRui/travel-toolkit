# Trip Buddy Program Contract

## Location and ownership

For a Travel Plan Bundle at `travel/`, keep the companion state under `travel/buddy/`:

```text
travel/
├── trip.json                 # canonical itinerary facts
└── buddy/
    ├── program.json          # canonical Buddy queue and delivery state
    ├── items/                # local generated sources, grouped by date
    └── sources/              # dated, expiring observations when needed
```

`program.json` never copies a reservation, route, or accommodation fact from `trip.json`. Reference stable IDs or a short `trip_ref` instead. Generated Markdown and remote documents are views of the program, not a second itinerary.

## Dynamic culture editor

Culture scheduling has two distinct layers:

- `items` holds dated **slots**, not prewritten articles. A culture slot becomes concrete only after its daily selection.
- `culture_editor` holds a deliberately bounded candidate pool: the number of cards each broad topic may receive, a preferred order, and durable exposure history.

This lets the programme stay coherent without turning a museum into an endless series. A large subject such as the Louvre might have four candidates and `max_cards: 4`; it cannot crowd out all other subjects. The pool may be planned ahead, but title, research, artwork, image, and document are generated only after the selector reads the current itinerary on the relevant day.

```json
{
  "culture_editor": {
    "selection": {
      "mode": "dynamic_daily",
      "max_cards": 22,
      "avoid_recent_topic_cards": 1
    },
    "topics": [
      {"id": "louvre", "target_cards": 4, "max_cards": 4}
    ],
    "candidates": [
      {
        "id": "louvre-winged-victory",
        "topic_id": "louvre",
        "title": "胜利女神没有头，却总在向前",
        "editorial_rank": 5,
        "trip_refs": ["item-louvre"]
      }
    ],
    "history": [
      {
        "candidate_id": "paris-island",
        "topic_id": "paris-origins",
        "date": "2026-09-03",
        "exposure": "preview",
        "counts_toward_quota": true
      }
    ]
  }
}
```

`history` records an already seen migrated card or a delivery that predates this programme. Normally, sent history is derived from culture items in `notified` state. `preview` does not count towards quota unless `counts_toward_quota` is explicitly true.

## Delivery timing

Keep phase-specific timing under `delivery.timing`. Each timing rule has an IANA `timezone` and `local_time` (`HH:MM`). Pre-departure may deliberately use the traveller's current timezone. Every `in_trip` rule must use the destination timezone in the linked Travel Plan Bundle.

```json
{
  "delivery": {
    "mode": "scheduled",
    "timing": {
      "pre_departure": {"timezone": "Asia/Shanghai", "local_time": "08:30"},
      "in_trip": {"timezone": "Europe/Paris", "local_time": "08:30"}
    }
  }
}
```

When the scheduler runs in a different timezone and cannot set a timezone itself, its host-time expression is only an implementation mapping. Record the mapping and exact date range with the scheduled task; regenerate it across a daylight-saving boundary. The selection and freshness checks always use the rule's local timezone, not the host's timezone.

When a selection is made, preserve it on the dated slot:

```json
{
  "id": "culture-slot-20260904",
  "kind": "culture",
  "trigger": {"type": "scheduled", "date": "2026-09-04"},
  "status": "drafted",
  "selection": {
    "candidate_id": "louvre-fortress",
    "topic_id": "louvre",
    "selected_at": "2026-09-04T00:30:00Z"
  }
}
```

Selection ranking is deterministic: keep under `max_cards`; avoid recent topics when possible; then prefer the candidate with the lowest `editorial_rank`. Remaining slots are a constraint, not a mandate to send stale or irrelevant content.

## Minimal program

```json
{
  "schema": "trip-buddy-program/v1",
  "trip_ref": "../trip.json",
  "timezone": "Europe/Paris",
  "language": "zh-CN",
  "delivery": {
    "mode": "manual",
    "profile_alias": "trip-updates",
    "document_first": true
  },
  "items": [
    {
      "id": "culture-20260904-01",
      "kind": "culture",
      "phase": "pre_departure",
      "trigger": {"type": "scheduled", "date": "2026-09-04"},
      "priority": "normal",
      "status": "planned",
      "trip_refs": ["day-paris-01"],
      "freshness": "durable"
    }
  ]
}
```

`profile_alias` is a semantic label only; resolve it from host-private configuration at delivery time through `travel-notify`. Never persist a chat ID, bot secret, session key, or user ID.

## Item kinds

| Kind | Purpose | Freshness | Can interrupt? |
|---|---|---|---|
| `culture` | Story-led art, history, place, or craft card | durable | no |
| `readiness` | Proposed preparation or deadline reminder | bounded by its stated deadline | no |
| `day_brief` | Current-day route, practical notes, weather and clothing | expires at day end | scheduled only |
| `disruption` | Verified, material impact assessment | source-defined and short-lived | only `alert` priority |

## Alert threshold

A disruption item becomes `alert` only if all are true:

1. It comes from an official operator, public authority, venue, carrier, or equally direct primary source.
2. It is tied to the traveller's current/next location and date, or a confirmed transport/reservation reference.
3. It changes a concrete decision: route, departure time, venue access, safety, or required preparation.
4. The item records source URL, `checked_at`, `valid_until`, impact, and fallback.

Generic weather news, social posts, or a forecast for the wrong city/date are not alerts.

## Delivery policy

- `manual`: prepare artifacts; no automatic document or message send.
- `scheduled`: may run at its configured cadence after explicit delivery approval.
- `alert_only`: normal content stays silent; only validated `alert` items may notify.

The default is `manual`. Changing delivery mode, recipient, or notification cadence requires explicit user confirmation. After an artifact is verified, build a `trip-buddy-notification/v1` request and pass it to `travel-notify`; adapters own platform-specific sends and receipts.
