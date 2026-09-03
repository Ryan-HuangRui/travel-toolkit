---
name: plan-travel-guide
description: "Explore, decide, build, validate, and export portable travel plans through a canonical Travel Plan Bundle. Uses a two-phase workflow: first compare event-informed trip skeletons from rough dates and unassigned cities, then build detailed transport, lodging, daily routes, attractions, restaurants, and reservations only after the user accepts the skeleton. Use for multi-day trip creation or revision, flexible-date festival or seasonal discovery, city-order and night allocation, nearby-date or city-placement proposals, itinerary comparison, confirmed booking and task tracking, Markdown or CSV artifacts, or continuing from an existing trip.json without depending on a specific repository or external service."
---

# Plan Travel Guide

Create evidence-backed travel plans without binding the workflow to a particular repository, map provider, booking platform, or note-taking system. Keep `trip.json` as the only canonical plan and compile human-readable views from it.

## Choose the operating mode

- Use **inline mode** for a focused question or comparison. Answer directly and do not create files unless requested.
- Use **workspace mode** for a complete itinerary, an ongoing planning project, or any request to save/update the plan. Create or update a Travel Plan Bundle.
- Use **export mode** only when the user requests an additional format or external synchronization. Keep the canonical data unchanged unless the export reveals a correction.

Never treat a recommendation as confirmed, a quoted price as paid, or an itinerary draft as accepted without user evidence.

## Choose the planning phase

- Use **exploration** when dates, cities, order, nights, or priorities are still being discussed. This is the default for rough ranges and “help me plan” requests.
- Use **detailed** only after the user accepts a trip skeleton: trip window, destination set, approximate nights, important city windows, and hard transport or lodging anchors.

The phase is independent of inline, workspace, and export modes. In exploration, research enough to compare strong skeletons and reveal date-sensitive opportunities; do not spend effort on hourly schedules, exact restaurants, or routine tickets. Present one recommended skeleton plus at most two materially different alternatives, then ask for the decisions that unlock the next phase. Never advance to `detailed` merely because one option looks best.

## Use a Travel Plan Bundle

Store a portable bundle in a user-selected directory. If no directory is specified for a full saved plan, use `travel-plans/<trip-id>/` under the current working directory and state that assumption.

The minimum bundle is:

```text
<trip-id>/
├── trip.json
├── itinerary.md
├── planning.md
├── budget.csv
└── sources.md
```

Read [references/artifact-contract.md](references/artifact-contract.md) completely before creating or structurally editing a bundle. Treat `trip.json` as canonical. Treat every other file as generated and replaceable.

Initialize a bundle with:

```bash
python3 scripts/init_trip.py OUTPUT_DIR \
  --title "France Trip 2026" \
  --start-date 2026-09-27 \
  --end-date 2026-10-07 \
  --date-flexibility tentative \
  --discovery-days-before 3 \
  --discovery-days-after 3 \
  --planning-phase exploration \
  --timezone Europe/Paris \
  --language zh-CN \
  --currency EUR
```

Do not overwrite an existing `trip.json`. Load it, preserve IDs and history-bearing records, increment `revision`, update `updated_at`, validate, and render again.

## Phase 1: Explore and decide the skeleton

1. Establish the current request. Do not continue answering an older lodging, restaurant, or route question after the user changes topics.
2. Collect only decision-shaping inputs: rough dates and flexibility, candidate cities, trip length, travelers, arrival/departure anchors, booked facts, budget band, pace, interests, must-do items, exclusions, and special occasions.
3. Separate confirmed facts, accepted decisions, candidates, open checks, and time-sensitive facts. Mark candidate city stays as `fixed`, `tentative`, or `unassigned`; do not invent dates or order.
4. Run destination discovery across candidate cities before fixing the route. Let confirmed standout events, seasonal conditions, and local character influence city selection, order, and nights.
5. Produce one recommended skeleton plus at most two alternatives. For each, compare city order, nights, rough travel load, event fit, major tradeoffs, and what would have to change.
6. Ask the user to decide only the unresolved choices that materially affect the skeleton. Keep all options proposed until accepted.
7. Stay in exploration if trip dates, destination set, city order, or nights remain materially open.

## Phase 2: Build the detailed plan

Enter this phase only after explicit skeleton acceptance.

1. Set `planning_phase` to `detailed`, record the accepted decisions, and assign or confirm the relevant city `stay_window` records.
2. Treat accepted decisions and booked reservations as anchors. Reopen them only when the user asks or new evidence creates a conflict.
3. Validate intercity transport and lodging areas, then fill daily geographic clusters, attractions, meals, rest, luggage handling, check-in, queues, last entry, daylight, and realistic buffers.
4. Refresh destination discovery against the accepted city windows. Recheck exact event dates, ticket release, sell-out risk, and whether earlier exploration assumptions remain current.
5. Apply the feasibility gate before promoting any item. Generate tasks for reservations and time-sensitive refreshes.
6. Read [references/research-checklists.md](references/research-checklists.md) for the needed modules and [references/source-and-privacy-policy.md](references/source-and-privacy-policy.md) whenever researching mutable or private facts.

## Run the destination-discovery pass

For every candidate or selected destination city:

1. Treat the supplied trip dates as the **core trip window**. Record whether they are `fixed`, `tentative`, or `unknown` plus allowed discovery days before and after. If trip dates are tentative or unknown and the user gives no tolerance, search three days before and after and state that assumption.
2. For each city, use its optional `stay_window`: `fixed` has anchored dates, `tentative` has movable working dates and its own tolerance, and `unassigned` has no dates yet. For an unassigned city, search across the core trip window so a standout event can become a scheduling anchor.
3. Search the applicable city or trip window for festivals, exhibitions, performances, concerts, sports, markets, public celebrations, temporary openings, and other scheduled events.
4. Search the permitted nearby-date window for standout events that could reasonably justify moving a tentative city stay or shifting or extending the trip. Do not broaden indefinitely.
5. Search the season for limited-time nature, food, wine, harvest, holiday, and regional experiences even when they are not single-date events.
6. Identify place-specific character that a generic landmark list misses: neighborhood rituals, local markets, signature food and drink, craft, architecture, scenic timing, transport experiences, and nearby traditions.
7. Check public holidays, closure patterns, major crowd drivers, and transport disruptions that could change either the current or proposed plan.
8. Rank discoveries by date fit, uniqueness, user interest, geographic fit, opportunity cost, ticket feasibility, pace, budget, and the cost of changing dates. Prefer a good in-window option over a marginally better option that requires replanning.
9. Keep useful discoveries in `candidates` with a discovery category, event window, `date_fit`, `date_confidence`, `route_fit`, `booking_timing`, place, notes, and source IDs. Resolve the comparison window from the city's `stay_window`; use the overall trip window only when the city is unassigned.
10. For a useful event in an unassigned city, propose placing that city stay around the event. For a nearby-date event, propose moving the tentative city stay or changing the trip window. Store the scope, change type, proposed window, minimum changed days, affected anchors, impact summary, and direct `decision_prompt` in `date_adjustment`.
11. Use `confirmed` date confidence only when the current year's dates are published. Mark recurring but unpublished annual events as `expected` or `unknown` and set their evidence to `needs_refresh`.
12. Never assign or change canonical trip or city dates merely because an event exists. Present the event and tradeoff, ask the user, and update dates only after explicit acceptance. Then record or supersede the related decision and revalidate all affected anchors.
13. Promote a discovery into a day item only after it passes the feasibility gate and the user accepts it. Create a task when tickets or a timed reservation require action.

Aim for one to three high-value discoveries per city rather than an exhaustive event dump. Nearby-date discoveries must clear a higher bar than in-window discoveries. It is valid to report that no strong match was found while still offering seasonal or local-character alternatives.

## Apply the feasibility gate

Before finalizing or promoting an item to `confirmed`, check:

- date, weekday, local time, and time zone;
- opening hours, last entry, reservation window, and closure risk;
- door-to-door transit time rather than advertised ride duration alone;
- check-in, checkout, luggage, airport/station, and accessibility friction;
- schedule overlaps, queue buffers, meals, rest, and realistic walking load;
- cancellation terms, total price, currency, and whether the price is quoted or paid;
- same-day and same-place overlap when comparing two itineraries;
- freshness and provenance for prices, availability, timetables, and events;
- whether a proposed date change conflicts with booked transport, lodging, leave, visas, other city stays, or non-refundable costs;
- a fallback for fragile or weather-dependent items.

Use `proposed`, `confirmed`, `booked`, `completed`, or `cancelled` for execution state. Use source freshness separately; do not demote a confirmed decision merely because an opening time needs refresh.

## Update the canonical plan

When the user confirms a change in workspace mode:

1. Update only the affected records in `trip.json`.
2. Preserve stable IDs for existing places, days, items, reservations, tasks, and decisions.
3. Append or supersede decisions instead of erasing the reasoning behind an earlier choice.
4. Add source IDs to externally verified facts.
5. Increment `revision` by one and set `updated_at` to an ISO 8601 timestamp.
6. Run validation:

```bash
python3 scripts/validate_trip.py PATH/TO/TRIP_OR_BUNDLE
```

7. Fix all errors. Review warnings rather than hiding them.
8. Regenerate derived artifacts:

```bash
python3 scripts/render_trip.py PATH/TO/TRIP_OR_BUNDLE
```

9. Report the canonical file, generated files, revision, important decisions, and unresolved checks.

## Handle workspace integrations

Keep the core workflow repository-independent. A workspace may provide instructions describing where to place the bundle or how to summarize confirmed changes in its own project files. Follow those instructions as an adapter layer, but never copy workspace-specific paths or rules into this skill.

External writes are opt-in:

- Do not update Notion, calendars, spreadsheets, email, booking services, or repositories unless the user explicitly asks.
- Treat those systems as adapters that consume `trip.json` or its generated views.
- Re-read and verify an external destination after a write when the tool supports it.
- Do not let an external export become a competing canonical source.

## Protect private information

Generate share-safe artifacts by default. Do not persist payment credentials, complete booking codes, personal contact details, passport data, private contract text, or unnecessarily precise private-home addresses.

If the user explicitly needs private operational details, keep them outside the standard bundle in `private.local.json`, warn that it must not be committed or shared, and exclude it from all normal rendering and export steps.

## Output style

Use the user's language. Lead with the recommended route or decision. For a full plan, include:

1. trip skeleton;
2. daily itinerary and transport;
3. in-window and nearby-date local events, seasonal experiences, and distinctive local character;
4. city-placement and date-adjustment options that require the user's decision;
5. confirmed bookings;
6. candidates and tradeoffs;
7. actionable tasks;
8. budget summary;
9. sources and freshness;
10. unresolved checks and fallbacks.

Keep inline answers proportional to the question. Do not generate Excel, PDF, images, calendar events, or external pages unless requested.

## Scripts

- `scripts/init_trip.py`: create a new bundle with explicit date flexibility without overwriting existing data.
- `scripts/validate_trip.py`: validate structure, references, dates, statuses, and schedule conflicts using only the Python standard library.
- `scripts/render_trip.py`: compile Markdown and CSV views from a valid `trip.json`.
