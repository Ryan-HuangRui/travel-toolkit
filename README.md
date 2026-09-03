# Travel Toolkit

An open-source, agent-native travel toolkit for planning trips, verifying day-to-day logistics, and supporting travellers before and during the journey.

The same skills are packaged for **OpenAI Codex / ChatGPT**, **Claude Code**, and **GitHub Copilot CLI**.

[中文说明](README.zh-CN.md)

## Quick start

### Claude Code

```bash
claude plugin marketplace add Ryan-HuangRui/travel-toolkit
claude plugin install travel-toolkit@travel-toolkit
```

### GitHub Copilot CLI

```bash
copilot plugin marketplace add Ryan-HuangRui/travel-toolkit
copilot plugin install travel-toolkit@travel-toolkit
```

### ChatGPT / Codex

Eligible managed-workspace admins can import this repository from **Workspace settings → Plugins → Add → Import marketplace**.

Use this repository as the source and leave the marketplace path empty:

```text
https://github.com/Ryan-HuangRui/travel-toolkit
```

See [docs/distribution.md](docs/distribution.md) for platform details, local testing, and release notes.

After installation, start with a natural request such as:

```text
Help me plan a 10-day France trip. I want Paris and the south of France,
I prefer a relaxed pace, and I want the itinerary to stay editable as I book things.
```

## Why this is different from a one-shot itinerary prompt

Travel Toolkit treats a trip as an evolving project rather than a single generated answer.

- Explore destination order, nights, seasonal opportunities, and tradeoffs before over-planning details.
- Keep accepted decisions, reservations, candidates, tasks, and evidence in one portable Travel Plan Bundle.
- Verify fragile POIs and travel legs with map providers instead of relying only on model intuition.
- Re-plan affected days when a booking or schedule changes without silently rewriting confirmed facts.
- Continue after planning with readiness checks, daily briefs, cultural context, and verified disruption alerts.

`trip.json` is the only canonical itinerary. Human-readable Markdown and CSV files are generated views and can be recreated at any time.

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

Map providers supply time-bound route evidence; Trip Buddy consumes the latest bundle and never silently rewrites confirmed itinerary facts.

## Included skills

- `plan-travel-guide`: explore a destination, decide the trip skeleton, build and validate a portable Travel Plan Bundle.
- `travel-maps-planner`: normalize places and verify routes with Google Maps or Amap.
- `trip-buddy`: coordinate pre-departure content, readiness, in-trip briefs, and verified disruptions.
- `travel-culture-card`, `travel-readiness`, `travel-day-brief`, `travel-disruption-watch`: focused Trip Buddy content skills.
- `travel-notify`: provider-neutral notification request and idempotency boundary.
- `travel-notify-feishu-cli`: optional bot-only Feishu IM adapter, dry-run by default.

## Portable bundle

A full saved trip uses a small, portable artifact set:

```text
<trip-id>/
├── trip.json
├── itinerary.md
├── planning.md
├── budget.csv
├── sources.md
└── buddy/              # optional Trip Buddy state
```

The bundle is deliberately independent of Notion, calendars, booking sites, or a particular agent host. External systems are adapters; they do not become competing sources of truth.

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

## Multi-agent packaging

The skills themselves live only once under `plugins/travel-toolkit/skills/`. Platform-specific metadata stays thin:

```text
.agents/plugins/marketplace.json
.claude-plugin/marketplace.json
plugins/travel-toolkit/.codex-plugin/plugin.json
plugins/travel-toolkit/.claude-plugin/plugin.json
plugins/travel-toolkit/skills/
```

This keeps behaviour shared across supported agents while allowing each host to discover the plugin using its native or compatible marketplace format.

## Development

The repository contains a synthetic bundle under `examples/synthetic-city-break/`. Validate the plugin and the included contracts before release:

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py plugins/travel-toolkit
python3 plugins/travel-toolkit/skills/plan-travel-guide/scripts/validate_trip.py examples/synthetic-city-break
python3 plugins/travel-toolkit/skills/travel-notify/scripts/validate_notification_request.py plugins/travel-toolkit/skills/travel-notify/references/notification-request.example.json
```

If Claude Code is installed locally, also validate the marketplace and plugin manifests with:

```bash
claude plugin validate .
```

See [docs/distribution.md](docs/distribution.md) before publishing a new version.

## License

Apache-2.0. This project is independent software and is not affiliated with OpenAI, Anthropic, GitHub, Google, Amap, or Feishu/Lark.
