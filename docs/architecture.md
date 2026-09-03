# Architecture

## Canonical ownership

| Layer | Owns | Does not own |
| --- | --- | --- |
| `plan-travel-guide` | itinerary decisions, Bundle revision, `trip.json` | platform notifications |
| `travel-maps-planner` | place and route evidence | canonical itinerary writes without confirmation |
| `trip-buddy` | content selection, delivery intent, Buddy state | route planning or platform credentials |
| `travel-notify` | platform-neutral notification contract | raw recipients or sends |
| delivery adapter | platform send and safe receipt | itinerary facts or editorial selection |

## Delivery state

`planned → drafted → source_verified → document_verified → sending → notified`

`sending` is intentionally protected. If an adapter cannot prove success, preserve the uncertain state and reconcile it; do not resend automatically.

## Scheduler boundary

Schedulers are deployment adapters. A host can use cron, cc-connect, GitHub Actions, or another runner, but each scheduled run must read the latest `trip.json`, use the destination timezone during travel, and honor the program's delivery mode. Scheduler configuration, recipient mappings, and credentials stay outside this repository.
