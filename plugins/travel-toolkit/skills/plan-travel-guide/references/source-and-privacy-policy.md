# Source and Privacy Policy

## Source priority

Use the strongest source available for each claim:

1. explicit user statement or booking evidence for personal facts;
2. official operator, venue, tourism board, restaurant, or event site;
3. map/place provider for location and route evidence;
4. booking/search platform for availability, price, and review signals;
5. reputable secondary source;
6. clearly labeled estimate.

Do not infer live capability from a connector name or an open browser tab. Verify that the available tool can actually retrieve the required data.

## Mutable facts

Browse or otherwise refresh facts that can change, including prices, inventory, schedules, opening hours, reservation rules, restaurant service, public transit, weather, and events.

Record `checked_at` and `freshness`. Mark facts that should be checked again near the travel date.

For destination discovery, prefer official city or tourism calendars, organizer and venue pages, museums, public institutions, market operators, sports organizations, and current-year event programs. Search both the current plan and the permitted nearby-date window when dates are flexible. A prior-year page may establish recurrence but cannot confirm the travel year's date or justify a date change by itself.

Do not let an older spreadsheet, export, or generated Markdown override a newer canonical fact.

## Evidence discipline

- Attach source IDs to externally verified day items, reservations, candidates, decisions, and budget entries.
- State uncertainty when a detail call times out or a search drifts off target.
- Prefer a returned, location-correct result over an unreliable secondary detail lookup.
- Keep direct quotations short and respect source licenses and copyright.

## Privacy defaults

The standard Travel Plan Bundle is share-safe by default. Do not persist:

- passwords, API keys, payment credentials, or bank data;
- passport, visa, or government identification numbers;
- complete booking or confirmation codes;
- personal phone numbers or private email addresses;
- private contract or email bodies;
- unnecessarily precise addresses for private homes;
- data about other travelers that is not required for planning.

Store general neighborhoods, public hotel addresses, sanitized cost/status facts, cancellation deadlines, and source descriptions when useful.

If the user explicitly requests private operational storage, put it in `private.local.json`, keep it outside normal rendering, and warn that it must not be committed or shared. Never create that file by default.

## External actions

Research and artifact generation do not authorize booking, purchasing, sending messages, changing calendars, updating Notion, or writing to other systems.

Perform an external write only when explicitly requested. Confirm the target and scope, apply the smallest change, and verify the result when possible.
