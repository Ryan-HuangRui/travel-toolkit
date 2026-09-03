# Notification Contract

The request is a short-lived delivery artifact, not a copy of `trip.json` or a credential store.

```json
{
  "schema": "trip-buddy-notification/v1",
  "id": "sample-trip:culture:2026-09-04",
  "kind": "culture",
  "recipient_profile": "trip-updates",
  "delivery_mode": "scheduled",
  "state": "sending",
  "authorized": true,
  "idempotency_key": "trip-buddy:sample-trip:culture:2026-09-04",
  "content": {
    "title": "D-22 | 一座城市从河中长出来",
    "body": "今日文化卡已准备好。",
    "artifact_url": "https://example.invalid/culture-card"
  }
}
```

Required fields are `schema`, `id`, `kind`, `recipient_profile`, `delivery_mode`, `state`, `authorized`, `idempotency_key`, and a `content` object with `title` and `body`. `recipient_profile` is an alias, never a raw platform recipient ID.

Allowed `delivery_mode` values are `manual`, `scheduled`, and `alert_only`. The adapter only sends a request with `state: "sending"`; an orchestrator owns state transitions.
