# Travel Research Checklists

Load only the sections relevant to the user's request.

## Research by planning phase

In `exploration`, research only facts that can change the trip skeleton: standout events, seasonal conditions, major closures, route-scale transport, rough lodging geography, and large cost differences. Do not optimize individual restaurants, ordinary attraction hours, or hourly routing yet.

In `detailed`, refresh the accepted skeleton and research exact transport, lodging, opening hours, ticket rules, restaurants, route transitions, buffers, and fallbacks. Recheck exploration evidence before relying on it operationally.

## Lodging

- Start from the itinerary segment and transport anchors, then choose an area before individual properties.
- Compare total price, cancellation, check-in, luggage storage, accessibility, elevator, air conditioning, private bathroom, kitchen, bed, noise, safety, and review reliability.
- Confirm that the location supports the first stop, last stop, station/airport, and major day trips.
- Distinguish a platform search result from live bookable inventory.
- When a platform cannot be searched reliably, use accessible sources and compare user-provided links or screenshots under the same criteria.
- Return one strong candidate first when requested; do not flood the user with a long list.

## Intercity transport

- Compare door-to-door time, not just flight or train duration.
- Include city-to-airport/station access, required arrival buffer, security, baggage, transfers, and arrival-to-lodging time.
- Check official operator channels first for timetable, baggage, fare, exchange, and refund rules.
- Prefer station names and through-ticket details that reduce ambiguous transfers.
- Treat purchased transport as a hard anchor unless the user asks to revisit it.

## Attractions and tickets

- Verify the exact visit date and weekday.
- Check the official site for opening hours, closure days, last entry, reservation rules, ticket release windows, and temporary restrictions.
- Classify each item as `book early`, `monitor`, or `walk in`.
- Keep arrival days light and avoid stacking multiple timed indoor attractions without buffer.
- Add a fallback for queues, weather, closures, or sold-out slots.

## Restaurants

- Tie the recommendation to the actual date, weekday, neighborhood, preceding activity, next destination, occasion, cuisine preference, and budget.
- Verify current dinner service rather than general opening hours.
- Check walking/transit time from the last activity and to the lodging.
- Consider sunset timing when a viewpoint precedes dinner.
- Offer a primary choice and a lower-friction fallback.

## Destination discovery and local character

Run this section for every overnight city in a complete workspace plan, even when the user does not explicitly ask for events.

### Core and nearby-date windows

- Treat supplied dates as the current core plan, not automatically as immutable dates or as the maximum research window.
- Record date flexibility as `fixed`, `tentative`, or `unknown`, with allowed discovery days before and after.
- Use the user's tolerance when provided. For tentative or unknown dates with no stated tolerance, use three days before and after and disclose the assumption.
- Record each destination city's `stay_window` as `fixed`, `tentative`, or `unassigned`. Fixed and tentative windows may have dates; an unassigned city deliberately has none.
- Search a fixed or tentative city window first, then its permitted nearby dates. For an unassigned city, search the overall trip window and let a strong event suggest where that city could fit.
- Check official city and tourism calendars, venue calendars, museums, performance halls, sports venues, festival organizers, markets, universities, and public institutions.
- Look for festivals, temporary exhibitions, concerts, theater, dance, sports, fairs, markets, parades, public celebrations, temporary openings, and neighborhood events.
- Separate current-year published dates from recurring annual events whose next dates are not yet published.
- Check venue, start/end time, admission, ticket release, sell-out risk, language accessibility, age restrictions, and route fit.
- Keep nearby-date events only when their distinctiveness plausibly justifies the date change. Do not expand the search window merely because no good result was found.
- Reject events that occur in the wider region but create disproportionate conflict with booked transfers, lodging, or full itinerary anchors.

### Seasonal and place-specific experiences

- Search for seasonal nature, harvest, food, wine, holiday, weather, and daylight experiences.
- Identify signature local food and drink, neighborhood markets, craft, architecture, scenic timing, public transport experiences, and cultural practices.
- Prefer experiences that are hard to reproduce elsewhere over generic top-ten attractions.
- Distinguish a real local practice from a tourism-marketing claim, and keep evidence for non-obvious recommendations.

### Ranking and representation

- Rank by date fit, uniqueness, user interest, route fit, opportunity cost, booking feasibility, pace, budget, and date-change cost.
- Store useful discoveries as candidates using categories such as `local_event`, `festival`, `performance`, `exhibition`, `sports`, `market`, `seasonal_experience`, `local_specialty`, `food_and_drink`, or `neighborhood_experience`.
- Record `start_date`, optional time window, `date_fit`, `date_confidence`, `route_fit`, `booking_timing`, `place_id`, notes, and source IDs.
- Compare an event with the referenced city's `stay_window`. If the city is unassigned, compare with the overall trip window and use `date_fit: within_trip_unassigned` for an event that could anchor the city stay.
- Use `date_confidence: confirmed` only when the current year's date is published. Use `expected` or `unknown` for recurring or incomplete calendars.
- Classify `date_fit` as `within_city_window`, `overlaps_city_window`, `within_trip_unassigned`, `nearby_before`, `nearby_after`, or `seasonal_flexible`.
- For a worthwhile `within_trip_unassigned`, `nearby_before`, or `nearby_after` result, record a `date_adjustment` with `scope`, `kind`, proposed dates, minimum changed days, affected IDs, an impact summary, and a direct decision prompt. Use `place_city_stay` when the proposal assigns dates to a previously unassigned city without changing the overall trip dates.
- Compare the current and proposed windows. State what moves, what remains anchored, incremental time or cost, and whether bookings must be changed.
- Present the nearby event as an option such as: “This event is two days after the current plan. Moving the city stay by two days would make it possible but affects X. Do you want to adjust the dates?”
- Never apply the proposed dates until the user explicitly accepts them. Keep the current itinerary unchanged while the decision is pending.
- Promote only accepted, feasible discoveries into day items. Create a task when booking action is required.
- Keep the final shortlist to one to three high-value discoveries per city; nearby-date options must clear a higher recommendation threshold than in-window options.

## Comparing itineraries

- Compare date plus location, not thematic similarity alone.
- Distinguish exact overlap, nearby overlap, route similarity on different dates, and no overlap.
- Do not recommend moving booked anchors merely to manufacture a match unless the user asks for change options.

## Feasibility review

- Validate local date, weekday, time zone, and daylight.
- Include immigration, baggage, luggage storage, check-in, meals, rest, queues, and transit buffers.
- Flag two scheduled items that overlap or require implausible travel.
- State which facts are estimates and which need same-day refresh.
