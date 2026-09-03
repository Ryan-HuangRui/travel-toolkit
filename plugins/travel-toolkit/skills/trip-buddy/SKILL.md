---
name: trip-buddy
description: Orchestrate a travel companion across preparation and travel days by planning culture stories, readiness reminders, daily briefs, and verified disruption alerts from a canonical Travel Plan Bundle. Use for trip-buddy setup, daily program planning, or coordinated travel notifications; not for initial itinerary planning.
---

# Trip Buddy

`trip-buddy` is the coordination layer around an accepted itinerary. It does not replace `plan-travel-guide`: the Travel Plan Bundle's `trip.json` remains the sole source of truth for places, reservations, daily plans, and confirmed travel facts.

Read [the program contract](references/program-contract.md) before creating or changing a Buddy program. Read the relevant child Skill only for the selected work item.

## Inputs and boundaries

1. Read project-level agent instructions when present, then resolve the active Travel Plan Bundle from the user's explicit path or workspace context. If `plan-travel-guide` created the plan without a custom location, look under `travel-plans/<trip-id>/`. Read `<bundle>/trip.json`; do not assume a repository-specific path.
2. A Buddy program lives at `<bundle>/buddy/program.json` and records content intent, cadence, delivery policy, item state, source freshness, and idempotency state. It must reference the trip bundle; it must not duplicate itinerary facts.
3. For culture, plan a bounded editorial pool rather than pre-writing a dispatch queue. Record topic quotas, ordered candidate stories, and the history of what the traveller has actually seen. On each eligible day, select the best story from the latest `trip.json`, remaining culture slots, per-topic quota, and recent delivery history; only then research and generate its artifact.
4. An older project without a Travel Plan Bundle may be inspected only through a read-only legacy adapter. Do not migrate it, attach a schedule, or send messages until the user explicitly adopts a Travel Plan Bundle.
5. Keep group/chat IDs, credentials, and private addresses outside Git. Resolve delivery profiles only through a host-private notification adapter configuration.
6. Child Skills never send messages. The orchestrator may issue a platform-neutral notification request only after the user has approved the recipient, sending identity, content shape, cadence, and delivery mode. Use `travel-notify` and the selected delivery adapter for actual delivery.

## Select the work item

Determine the trip phase in the destination timezone, then select the highest-priority eligible item:

- `pre_departure`: culture stories and deadline-bound readiness items.
- `departure_window`: packing, document, transfer, and current-condition checks.
- `in_trip`: one daily brief for the current itinerary day; culture remains a separate optional item.
- `post_trip`: no automatic notices unless the user enables a reflection or archive item.
- `event`: a disruption alert only when it is verified, place/date-specific, and materially affects a confirmed or accepted plan.

For a `culture` slot, do not treat its scheduled date as a preselected article. Use the editorial pool to select on the day:

1. Read the current `trip.json` and exclude candidates whose referenced facts are no longer present or relevant.
2. Count only delivered items and explicit history records marked as quota-consuming; a generated preview is not a sent notification unless it is deliberately marked as such.
3. Respect each topic's `max_cards`, avoid a recently used topic where an alternative exists, and prefer the next eligible candidate in editorial order.
4. Rebalance against the remaining eligible culture slots. If the plan changed or slots are no longer sufficient, choose the most relevant available candidate rather than trying to exhaust an obsolete plan.
5. Persist the selected candidate on that day's slot before drafting, so a later retry cannot silently select a different story.

Use `scripts/select_culture_topic.py program.json --date YYYY-MM-DD` to preview a selection, and add `--apply` only when the daily run is ready to reserve that candidate. For a first-run dry-run that deliberately disregards earlier preview cards, add `--ignore-preview-history`; it never disregards notified cards.

Use these child Skills:

- `travel-culture-card` for a self-contained cultural or art story.
- `travel-readiness` for an actionable proposed checklist.
- `travel-day-brief` for a dated practical briefing.
- `travel-disruption-watch` for a source-bounded impact assessment.

## Timezone rule

The pre-departure sender may use the traveller's current location only when the programme says so. From the destination arrival date through departure, resolve both the calendar day and the configured delivery time in the destination timezone from `trip.json` / `program.json`; never use the automation host's clock as a proxy. If the host scheduler cannot attach an IANA timezone, configure its UTC/host-time mapping for the exact travel-date range and recheck any DST boundary before enabling it.

## Delivery contract

1. Generate and validate the local source artifact first.
2. If a document is requested, write it silently and fetch it back; compare title and required sections.
3. Write the item state to `document_verified` only after readback.
4. Send at most one concise notification per item using a stable idempotency key. Before visible delivery, record `sending`; never automatically retry an uncertain send.
5. A failed research, document, readback, validation, or send attempt is not a successful item and must not be described as one.

## State changes

- Advice and readiness findings start as `proposed`. Do not create or modify external task systems unless the user explicitly confirms the promotion.
- Use `planned → drafted → source_verified → document_verified → sending → notified` for delivered items. `sending` is a protected state requiring reconciliation before another send.
- Store time-sensitive source observations with `checked_at` and `valid_until`; do not write them back as durable itinerary facts.

## Validation

From the `trip-buddy` skill directory, run:

```bash
python3 scripts/validate_program.py PATH/TO/BUNDLE/buddy/program.json
```

Run the Travel Plan Bundle validator after any confirmed itinerary update. Validate the Buddy program separately after its own changes.
