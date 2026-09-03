# Travel Toolkit

An open-source Codex plugin for planning a trip, verifying day-to-day logistics, and supporting travellers before and during the journey.

## Workflow

```text
rough idea → plan-travel-guide → Travel Plan Bundle (trip.json)
                                  ↑
                    travel-maps-planner verifies places and routes
                                  ↓
                            trip-buddy
              culture / readiness / daily brief / disruption watch
                                  ↓
                           travel-notify
                                  ↓
                  optional platform adapter (Feishu CLI first)
```

`trip.json` is the only canonical itinerary. Map providers supply time-bound route evidence; Trip Buddy consumes the latest bundle and never silently rewrites confirmed itinerary facts.

## Included skills

- `plan-travel-guide`: explore a destination, decide the skeleton, build and validate a portable Travel Plan Bundle.
- `travel-maps-planner`: normalize places and verify routes with Google Maps or Amap.
- `trip-buddy`: coordinate pre-departure content, readiness, in-trip briefs, and verified disruptions.
- `travel-culture-card`, `travel-readiness`, `travel-day-brief`, `travel-disruption-watch`: focused Trip Buddy content skills.
- `travel-notify`: provider-neutral notification request and idempotency boundary.
- `travel-notify-feishu-cli`: optional bot-only Feishu IM adapter, dry-run by default.

## Map providers

Google Maps is the global default. Amap is included for mainland-China POI and routing and uses GCJ-02 for domestic Web Service endpoints. Amap overseas service requires separate provider entitlement and WGS84 coordinates; the adapter requires `--international` so coordinate systems cannot be mixed accidentally.

Set secrets only in your local environment:

```bash
export GOOGLE_MAPS_API_KEY=...
export AMAP_API_KEY=...
```

Never commit keys, profile mappings, booking references, exact private addresses, or real itinerary exports. See [docs/integrations.md](docs/integrations.md).

## Notifications

The core toolkit generates a validated notification request only. It does not send automatically. The Feishu adapter requires a locally configured `lark-cli` bot, a private recipient profile mapping, explicit user authorization, `state: "sending"`, and a stable idempotency key. Document publication is intentionally a separate adapter from message delivery.

## Development

The repository contains a synthetic bundle under `examples/synthetic-city-break/`. Validate the plugin and the included contracts before release:

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py plugins/travel-toolkit
python3 plugins/travel-toolkit/skills/plan-travel-guide/scripts/validate_trip.py examples/synthetic-city-break
python3 plugins/travel-toolkit/skills/travel-notify/scripts/validate_notification_request.py plugins/travel-toolkit/skills/travel-notify/references/notification-request.example.json
```

This repository is a source package. Test it in a local marketplace before publishing or submitting it to a plugin directory.

## License

Apache-2.0. This project is independent software and is not affiliated with Google, Amap, Feishu/Lark, or OpenAI.
