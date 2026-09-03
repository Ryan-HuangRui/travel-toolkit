#!/usr/bin/env python3
"""Validate a Travel Plan Bundle using only the Python standard library."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

TOP_LEVEL_LISTS = (
    "constraints",
    "places",
    "decisions",
    "days",
    "reservations",
    "candidates",
    "tasks",
    "budget",
    "sources",
)
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
TIME_RE = re.compile(r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
ITEM_TYPES = {"visit", "meal", "transfer", "checkin", "checkout", "event", "rest", "free_time", "other"}
EXECUTION_STATES = {"proposed", "confirmed", "booked", "completed", "cancelled"}
DECISION_STATES = {"proposed", "accepted", "rejected", "superseded"}
CANDIDATE_STATES = {"shortlisted", "recommended", "selected", "rejected"}
TASK_STATES = {"todo", "doing", "waiting", "blocked", "done", "dropped"}
BUDGET_STATES = {"estimated", "quoted", "paid", "refunded", "cancelled"}
FRESHNESS_STATES = {"current", "needs_refresh", "unknown"}
SOURCE_TYPES = {"user_statement", "official_site", "map", "booking_platform", "email", "calendar", "document", "estimate", "other"}
DATE_CONFIDENCE_STATES = {"confirmed", "expected", "unknown"}
ROUTE_FIT_STATES = {"direct", "nearby", "detour", "conflict", "unknown"}
BOOKING_TIMING_STATES = {"book_early", "monitor", "walk_in", "not_applicable"}
DATE_FLEXIBILITY_STATES = {"fixed", "tentative", "unknown"}
PLANNING_PHASES = {"exploration", "detailed"}
STAY_WINDOW_STATES = {"fixed", "tentative", "unassigned"}
DATE_FIT_STATES = {
    "within_city_window",
    "overlaps_city_window",
    "within_trip_unassigned",
    "nearby_before",
    "nearby_after",
    "seasonal_flexible",
    "within_trip",
    "overlaps_trip",
}
ADJUSTMENT_SCOPES = {"trip", "city_stay"}
ADJUSTMENT_KINDS = {"shift", "extend_start", "extend_end", "place_city_stay", "move_city_stay", "reorder_route"}
DISCOVERY_CATEGORIES = {
    "local_event",
    "festival",
    "performance",
    "exhibition",
    "sports",
    "market",
    "seasonal_experience",
    "local_specialty",
    "food_and_drink",
    "neighborhood_experience",
}


def resolve_trip_path(path: Path) -> Path:
    path = path.resolve()
    return path / "trip.json" if path.is_dir() else path


def load_trip(path: Path) -> dict[str, Any]:
    trip_path = resolve_trip_path(path)
    with trip_path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("trip.json root must be an object")
    return value


def parse_date(value: Any, field: str, errors: list[str]) -> date | None:
    if not isinstance(value, str):
        errors.append(f"{field} must be an ISO date string")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{field} is not a valid ISO date: {value}")
        return None


def parse_timestamp(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{field} must be an ISO 8601 string")
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} is not valid ISO 8601: {value}")


def minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def validate_bundle(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if data.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")
    if not isinstance(data.get("revision"), int) or data.get("revision", -1) < 0:
        errors.append("revision must be a non-negative integer")
    parse_timestamp(data.get("updated_at"), "updated_at", errors)

    trip = data.get("trip")
    if not isinstance(trip, dict):
        errors.append("trip must be an object")
        trip = {}
    for field in ("id", "title", "start_date", "end_date", "timezone", "language", "currency"):
        if not trip.get(field):
            errors.append(f"trip.{field} is required")
    if trip.get("id") and not ID_RE.fullmatch(str(trip["id"])):
        errors.append("trip.id must use lowercase letters, numbers, hyphens, or underscores")
    if trip.get("currency") and not re.fullmatch(r"[A-Z]{3}", str(trip["currency"])):
        errors.append("trip.currency must be a three-letter uppercase code")
    planning_phase = trip.get("planning_phase")
    if planning_phase is None:
        warnings.append("trip.planning_phase is missing; use exploration or detailed")
    elif planning_phase not in PLANNING_PHASES:
        errors.append("trip.planning_phase is invalid")
    start = parse_date(trip.get("start_date"), "trip.start_date", errors)
    end = parse_date(trip.get("end_date"), "trip.end_date", errors)
    if start and end and end < start:
        errors.append("trip.end_date is before trip.start_date")

    flexibility = trip.get("date_flexibility")
    flexibility_status = None
    discovery_days_before = 0
    discovery_days_after = 0
    if flexibility is not None:
        if not isinstance(flexibility, dict):
            errors.append("trip.date_flexibility must be an object")
        else:
            flexibility_status = flexibility.get("status")
            if flexibility_status not in DATE_FLEXIBILITY_STATES:
                errors.append("trip.date_flexibility.status is invalid")
            for field_name in ("days_before", "days_after"):
                value = flexibility.get(field_name)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    errors.append(f"trip.date_flexibility.{field_name} must be a non-negative integer")
                elif field_name == "days_before":
                    discovery_days_before = value
                else:
                    discovery_days_after = value
            if flexibility_status == "fixed" and (discovery_days_before or discovery_days_after):
                warnings.append("trip dates are fixed but the nearby-date discovery window is non-zero")
    else:
        warnings.append("trip.date_flexibility is missing; nearby-date discovery window is undefined")
    discovery_start = start - timedelta(days=discovery_days_before) if start else None
    discovery_end = end + timedelta(days=discovery_days_after) if end else None

    for key in TOP_LEVEL_LISTS:
        if not isinstance(data.get(key), list):
            errors.append(f"{key} must be an array")
            data[key] = []
    if planning_phase == "detailed" and not data["days"]:
        warnings.append("detailed planning phase has no day records")

    seen_ids: dict[str, str] = {}

    def register(record: Any, location: str) -> str | None:
        if not isinstance(record, dict):
            errors.append(f"{location} must be an object")
            return None
        record_id = record.get("id")
        if not isinstance(record_id, str) or not ID_RE.fullmatch(record_id):
            errors.append(f"{location}.id is missing or invalid")
            return None
        if record_id in seen_ids:
            errors.append(f"duplicate id {record_id!r} at {location}; first seen at {seen_ids[record_id]}")
        else:
            seen_ids[record_id] = location
        return record_id

    for key in ("constraints", "places", "decisions", "reservations", "candidates", "tasks", "budget", "sources"):
        for index, record in enumerate(data[key]):
            register(record, f"{key}[{index}]")

    places_by_id = {
        record.get("id"): record
        for record in data["places"]
        if isinstance(record, dict) and record.get("id")
    }
    place_ids = set(places_by_id)
    source_ids = {record.get("id") for record in data["sources"] if isinstance(record, dict)}
    sources_by_id = {
        record.get("id"): record
        for record in data["sources"]
        if isinstance(record, dict) and record.get("id")
    }
    stay_windows_by_place: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(data["places"]):
        if not isinstance(record, dict) or not record.get("id"):
            continue
        stay_window = record.get("stay_window")
        if stay_window is None:
            continue
        if not isinstance(stay_window, dict):
            errors.append(f"places[{index}].stay_window must be an object")
            continue
        status = stay_window.get("status")
        if status not in STAY_WINDOW_STATES:
            errors.append(f"places[{index}].stay_window.status is invalid")
        window_start = None
        window_end = None
        if stay_window.get("start_date"):
            window_start = parse_date(stay_window.get("start_date"), f"places[{index}].stay_window.start_date", errors)
        if stay_window.get("end_date"):
            window_end = parse_date(stay_window.get("end_date"), f"places[{index}].stay_window.end_date", errors)
        if window_start and window_end and window_end < window_start:
            errors.append(f"places[{index}].stay_window.end_date is before start_date")
        window_days: dict[str, int] = {}
        for field_name in ("days_before", "days_after"):
            value = stay_window.get(field_name)
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                errors.append(f"places[{index}].stay_window.{field_name} must be a non-negative integer")
            elif isinstance(value, int):
                window_days[field_name] = value
        if status in {"fixed", "tentative"} and (not window_start or not window_end):
            warnings.append(f"places[{index}].stay_window {status} status is missing dates")
        if status == "unassigned" and (window_start or window_end):
            warnings.append(f"places[{index}].stay_window unassigned status should not contain dates")
        if status == "fixed" and (window_days.get("days_before", 0) or window_days.get("days_after", 0)):
            warnings.append(f"places[{index}].stay_window fixed status has non-zero flexibility")
        if planning_phase == "detailed" and status == "unassigned":
            warnings.append(f"places[{index}] remains unassigned in detailed planning phase")
        stay_windows_by_place[record["id"]] = {
            "status": status,
            "start": window_start,
            "end": window_end,
            "days_before": window_days.get("days_before", 0 if status == "fixed" else discovery_days_before),
            "days_after": window_days.get("days_after", 0 if status == "fixed" else discovery_days_after),
        }

    def validate_refs(record: dict[str, Any], location: str) -> None:
        place_id = record.get("place_id")
        if place_id and place_id not in place_ids:
            errors.append(f"{location}.place_id references unknown place {place_id!r}")
        refs = record.get("source_ids", [])
        if not isinstance(refs, list):
            errors.append(f"{location}.source_ids must be an array")
        else:
            for source_id in refs:
                if source_id not in source_ids:
                    errors.append(f"{location}.source_ids references unknown source {source_id!r}")

    previous_day: date | None = None
    day_dates: set[date] = set()
    for day_index, day in enumerate(data["days"]):
        location = f"days[{day_index}]"
        if not isinstance(day, dict):
            errors.append(f"{location} must be an object")
            continue
        day_date = parse_date(day.get("date"), f"{location}.date", errors)
        if day_date:
            if start and day_date < start or end and day_date > end:
                errors.append(f"{location}.date is outside the trip range")
            if day_date in day_dates:
                errors.append(f"duplicate day date {day_date.isoformat()}")
            day_dates.add(day_date)
            if previous_day and day_date < previous_day:
                warnings.append(f"{location}.date is out of chronological order")
            previous_day = day_date
        base_place = day.get("base_place_id")
        if base_place and base_place not in place_ids:
            errors.append(f"{location}.base_place_id references unknown place {base_place!r}")
        items = day.get("items")
        if not isinstance(items, list):
            errors.append(f"{location}.items must be an array")
            continue
        scheduled: list[tuple[int, int, str]] = []
        for item_index, item in enumerate(items):
            item_location = f"{location}.items[{item_index}]"
            if not isinstance(item, dict):
                errors.append(f"{item_location} must be an object")
                continue
            register(item, item_location)
            if item.get("type") not in ITEM_TYPES:
                errors.append(f"{item_location}.type is invalid")
            if item.get("status") not in EXECUTION_STATES:
                errors.append(f"{item_location}.status is invalid")
            if not item.get("title"):
                errors.append(f"{item_location}.title is required")
            validate_refs(item, item_location)
            start_time = item.get("start_time")
            end_time = item.get("end_time")
            for field_name, value in (("start_time", start_time), ("end_time", end_time)):
                if value is not None and (not isinstance(value, str) or not TIME_RE.fullmatch(value)):
                    errors.append(f"{item_location}.{field_name} must use HH:MM")
            if isinstance(start_time, str) and TIME_RE.fullmatch(start_time) and isinstance(end_time, str) and TIME_RE.fullmatch(end_time):
                start_minute, end_minute = minutes(start_time), minutes(end_time)
                if end_minute <= start_minute:
                    errors.append(f"{item_location}.end_time must be after start_time")
                elif item.get("status") in {"confirmed", "booked"} and item.get("type") != "free_time":
                    scheduled.append((start_minute, end_minute, str(item.get("id", item_location))))
        scheduled.sort()
        for previous, current in zip(scheduled, scheduled[1:]):
            if current[0] < previous[1]:
                warnings.append(f"schedule overlap on {day.get('date')}: {previous[2]} and {current[2]}")

    for index, record in enumerate(data["decisions"]):
        if isinstance(record, dict):
            if record.get("status") not in DECISION_STATES:
                errors.append(f"decisions[{index}].status is invalid")
            validate_refs(record, f"decisions[{index}]")
    for index, record in enumerate(data["reservations"]):
        if isinstance(record, dict):
            if record.get("status") not in EXECUTION_STATES:
                errors.append(f"reservations[{index}].status is invalid")
            validate_refs(record, f"reservations[{index}]")
            if record.get("status") in {"confirmed", "booked"} and not record.get("source_ids"):
                warnings.append(f"reservations[{index}] is {record.get('status')} without source evidence")
    for index, record in enumerate(data["candidates"]):
        if isinstance(record, dict):
            if record.get("status") not in CANDIDATE_STATES:
                errors.append(f"candidates[{index}].status is invalid")
            validate_refs(record, f"candidates[{index}]")
            candidate_start = None
            candidate_end = None
            if record.get("start_date"):
                candidate_start = parse_date(record.get("start_date"), f"candidates[{index}].start_date", errors)
            if record.get("end_date"):
                candidate_end = parse_date(record.get("end_date"), f"candidates[{index}].end_date", errors)
            if candidate_start and candidate_end and candidate_end < candidate_start:
                errors.append(f"candidates[{index}].end_date is before start_date")
            stay_window = stay_windows_by_place.get(record.get("place_id"))
            window_status = "unassigned"
            current_window_start = start
            current_window_end = end
            window_days_before = discovery_days_before
            window_days_after = discovery_days_after
            if stay_window:
                window_status = stay_window.get("status")
                if window_status in {"fixed", "tentative"}:
                    current_window_start = stay_window.get("start")
                    current_window_end = stay_window.get("end")
                    window_days_before = stay_window.get("days_before", 0)
                    window_days_after = stay_window.get("days_after", 0)
            elif record.get("current_window_start_date") or record.get("current_window_end_date"):
                window_status = "tentative"
                if record.get("current_window_start_date"):
                    current_window_start = parse_date(record.get("current_window_start_date"), f"candidates[{index}].current_window_start_date", errors)
                if record.get("current_window_end_date"):
                    current_window_end = parse_date(record.get("current_window_end_date"), f"candidates[{index}].current_window_end_date", errors)
            if current_window_start and current_window_end and current_window_end < current_window_start:
                errors.append(f"candidates[{index}].current_window_end_date is before current_window_start_date")
            candidate_discovery_start = current_window_start - timedelta(days=window_days_before) if current_window_start else discovery_start
            candidate_discovery_end = current_window_end + timedelta(days=window_days_after) if current_window_end else discovery_end
            for field_name in ("start_time", "end_time"):
                value = record.get(field_name)
                if value is not None and (not isinstance(value, str) or not TIME_RE.fullmatch(value)):
                    errors.append(f"candidates[{index}].{field_name} must use HH:MM")
            candidate_start_time = record.get("start_time")
            candidate_end_time = record.get("end_time")
            if (
                isinstance(candidate_start_time, str)
                and TIME_RE.fullmatch(candidate_start_time)
                and isinstance(candidate_end_time, str)
                and TIME_RE.fullmatch(candidate_end_time)
                and (not candidate_start or not candidate_end or candidate_start == candidate_end)
                and minutes(candidate_end_time) <= minutes(candidate_start_time)
            ):
                errors.append(f"candidates[{index}].end_time must be after start_time for a same-day window")
            if record.get("date_confidence") and record.get("date_confidence") not in DATE_CONFIDENCE_STATES:
                errors.append(f"candidates[{index}].date_confidence is invalid")
            if record.get("date_fit") and record.get("date_fit") not in DATE_FIT_STATES:
                errors.append(f"candidates[{index}].date_fit is invalid")
            if record.get("route_fit") and record.get("route_fit") not in ROUTE_FIT_STATES:
                errors.append(f"candidates[{index}].route_fit is invalid")
            if record.get("booking_timing") and record.get("booking_timing") not in BOOKING_TIMING_STATES:
                errors.append(f"candidates[{index}].booking_timing is invalid")
            if record.get("category") in DISCOVERY_CATEGORIES:
                date_fit = record.get("date_fit")
                adjustment = record.get("date_adjustment")
                if not record.get("date_confidence"):
                    warnings.append(f"candidates[{index}] discovery is missing date_confidence")
                if not date_fit:
                    warnings.append(f"candidates[{index}] discovery is missing date_fit")
                if not record.get("source_ids"):
                    warnings.append(f"candidates[{index}] discovery has no source evidence")
                if record.get("date_confidence") == "confirmed" and not candidate_start:
                    warnings.append(f"candidates[{index}] has confirmed date confidence without start_date")
                if record.get("date_confidence") == "confirmed" and not record.get("source_ids"):
                    warnings.append(f"candidates[{index}] has confirmed date confidence without source evidence")
                if record.get("date_confidence") == "confirmed" and record.get("source_ids"):
                    evidence = [sources_by_id.get(source_id) for source_id in record.get("source_ids", [])]
                    if evidence and all(source and source.get("freshness") != "current" for source in evidence):
                        warnings.append(f"candidates[{index}] has confirmed date confidence without a current source")
                if date_fit in {"within_city_window", "within_trip"} and current_window_start and current_window_end and candidate_start and candidate_end:
                    if candidate_start < current_window_start or candidate_end > current_window_end:
                        warnings.append(f"candidates[{index}] date_fit does not fit inside the current city window")
                    if window_status == "unassigned" and date_fit == "within_city_window":
                        warnings.append(f"candidates[{index}] uses within_city_window for an unassigned city")
                if date_fit in {"overlaps_city_window", "overlaps_trip"} and current_window_start and current_window_end and candidate_start and candidate_end:
                    if candidate_end < current_window_start or candidate_start > current_window_end:
                        warnings.append(f"candidates[{index}] date_fit does not overlap the current city window")
                if date_fit == "within_trip_unassigned":
                    if window_status != "unassigned":
                        warnings.append(f"candidates[{index}] uses within_trip_unassigned for a city with assigned dates")
                    if start and end and candidate_start and candidate_end and (candidate_start < start or candidate_end > end):
                        warnings.append(f"candidates[{index}] within_trip_unassigned event does not fit inside the trip window")
                if date_fit == "nearby_before":
                    if candidate_end and current_window_start and candidate_end >= current_window_start:
                        warnings.append(f"candidates[{index}] date_fit nearby_before is inconsistent with its dates")
                    if candidate_start and candidate_discovery_start and candidate_start < candidate_discovery_start:
                        warnings.append(f"candidates[{index}] discovery is before the permitted nearby-date window")
                if date_fit == "nearby_after":
                    if candidate_start and current_window_end and candidate_start <= current_window_end:
                        warnings.append(f"candidates[{index}] date_fit nearby_after is inconsistent with its dates")
                    if candidate_end and candidate_discovery_end and candidate_end > candidate_discovery_end:
                        warnings.append(f"candidates[{index}] discovery is after the permitted nearby-date window")
                if date_fit in {"within_trip_unassigned", "nearby_before", "nearby_after"} and not isinstance(adjustment, dict):
                    warnings.append(f"candidates[{index}] discovery that can shape dates is missing date_adjustment")
                if (
                    date_fit in {"nearby_before", "nearby_after"}
                    and flexibility_status == "fixed"
                    and (not isinstance(adjustment, dict) or adjustment.get("scope") == "trip")
                ):
                    warnings.append(f"candidates[{index}] proposes changing fixed trip dates")
                if adjustment is not None:
                    if not isinstance(adjustment, dict):
                        errors.append(f"candidates[{index}].date_adjustment must be an object")
                    else:
                        if adjustment.get("scope") not in ADJUSTMENT_SCOPES:
                            errors.append(f"candidates[{index}].date_adjustment.scope is invalid")
                        if adjustment.get("kind") not in ADJUSTMENT_KINDS:
                            errors.append(f"candidates[{index}].date_adjustment.kind is invalid")
                        if date_fit == "within_trip_unassigned" and adjustment.get("kind") != "place_city_stay":
                            warnings.append(f"candidates[{index}] unassigned city should normally use place_city_stay")
                        proposed_start = parse_date(adjustment.get("proposed_start_date"), f"candidates[{index}].date_adjustment.proposed_start_date", errors)
                        proposed_end = parse_date(adjustment.get("proposed_end_date"), f"candidates[{index}].date_adjustment.proposed_end_date", errors)
                        if proposed_start and proposed_end and proposed_end < proposed_start:
                            errors.append(f"candidates[{index}].date_adjustment proposed end is before start")
                        minimum_change_days = adjustment.get("minimum_change_days")
                        if not isinstance(minimum_change_days, int) or isinstance(minimum_change_days, bool) or minimum_change_days < 0:
                            errors.append(f"candidates[{index}].date_adjustment.minimum_change_days must be a non-negative integer")
                        affected_ids = adjustment.get("affected_ids", [])
                        if not isinstance(affected_ids, list):
                            errors.append(f"candidates[{index}].date_adjustment.affected_ids must be an array")
                        else:
                            for affected_id in affected_ids:
                                if affected_id not in seen_ids:
                                    errors.append(f"candidates[{index}].date_adjustment.affected_ids references unknown id {affected_id!r}")
                        if not adjustment.get("impact_summary"):
                            warnings.append(f"candidates[{index}].date_adjustment is missing impact_summary")
                        if not adjustment.get("decision_prompt"):
                            warnings.append(f"candidates[{index}].date_adjustment is missing decision_prompt")
    for index, record in enumerate(data["tasks"]):
        if isinstance(record, dict):
            if record.get("status") not in TASK_STATES:
                errors.append(f"tasks[{index}].status is invalid")
            due = record.get("due_date")
            if due:
                parse_date(due, f"tasks[{index}].due_date", errors)
            related_ids = record.get("related_ids", [])
            if not isinstance(related_ids, list):
                errors.append(f"tasks[{index}].related_ids must be an array")
            else:
                for related_id in related_ids:
                    if related_id not in seen_ids:
                        errors.append(f"tasks[{index}].related_ids references unknown id {related_id!r}")
    for index, record in enumerate(data["budget"]):
        if isinstance(record, dict):
            if record.get("status") not in BUDGET_STATES:
                errors.append(f"budget[{index}].status is invalid")
            if not re.fullmatch(r"[A-Z]{3}", str(record.get("currency", ""))):
                errors.append(f"budget[{index}].currency is invalid")
            if not isinstance(record.get("amount"), (int, float)):
                errors.append(f"budget[{index}].amount must be numeric")
            validate_refs(record, f"budget[{index}]")
            related_id = record.get("related_id")
            if related_id and related_id not in seen_ids:
                errors.append(f"budget[{index}].related_id references unknown id {related_id!r}")
    for index, record in enumerate(data["sources"]):
        if isinstance(record, dict):
            if record.get("type") not in SOURCE_TYPES:
                errors.append(f"sources[{index}].type is invalid")
            if record.get("freshness") not in FRESHNESS_STATES:
                errors.append(f"sources[{index}].freshness is invalid")
            if record.get("checked_at"):
                parse_timestamp(record.get("checked_at"), f"sources[{index}].checked_at", errors)

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="trip.json or its bundle directory")
    args = parser.parse_args()
    try:
        data = load_trip(args.path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    errors, warnings = validate_bundle(data)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        print(f"Validation failed with {len(errors)} error(s) and {len(warnings)} warning(s).", file=sys.stderr)
        return 1
    print(f"Travel plan is valid with {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
