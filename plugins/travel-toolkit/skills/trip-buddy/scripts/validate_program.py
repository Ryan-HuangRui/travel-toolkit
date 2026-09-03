#!/usr/bin/env python3
"""Validate the portable, non-secret state of a Trip Buddy program."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


KINDS = {"culture", "readiness", "day_brief", "disruption"}
PHASES = {"pre_departure", "departure_window", "in_trip", "post_trip", "event"}
STATUSES = {"planned", "drafted", "source_verified", "document_verified", "sending", "notified", "skipped", "failed"}
DELIVERY_MODES = {"manual", "scheduled", "alert_only"}
SECRET_KEYS = {"chat_id", "session_key", "app_secret", "bot_secret", "access_token", "user_id"}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def valid_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def valid_local_time(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value) is not None


def validate_timing(delivery: object, errors: list[str]) -> None:
    if not isinstance(delivery, dict) or "timing" not in delivery:
        return
    timing = delivery["timing"]
    if not isinstance(timing, dict):
        fail(errors, "delivery.timing must be an object")
        return
    for phase, rule in timing.items():
        prefix = f"delivery.timing.{phase}"
        if phase not in {"pre_departure", "departure_window", "in_trip", "post_trip"}:
            fail(errors, f"{prefix} uses an invalid phase")
            continue
        if not isinstance(rule, dict):
            fail(errors, f"{prefix} must be an object")
            continue
        zone = rule.get("timezone")
        if not isinstance(zone, str):
            fail(errors, f"{prefix}.timezone must be an IANA timezone")
        else:
            try:
                ZoneInfo(zone)
            except ZoneInfoNotFoundError:
                fail(errors, f"{prefix}.timezone is not a valid IANA timezone")
        if not valid_local_time(rule.get("local_time")):
            fail(errors, f"{prefix}.local_time must use HH:MM")


def trip_record_ids(trip_path: Path) -> set[str]:
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    result: set[str] = set()
    for key in ("constraints", "places", "decisions", "reservations", "candidates", "tasks", "budget", "sources"):
        for record in trip.get(key, []):
            if isinstance(record, dict) and isinstance(record.get("id"), str):
                result.add(record["id"])
    for day in trip.get("days", []):
        for item in day.get("items", []) if isinstance(day, dict) else []:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                result.add(item["id"])
    return result


def validate_culture_editor(editor: object, trip_ids: set[str], errors: list[str]) -> tuple[set[str], dict[str, int]]:
    if editor is None:
        return set(), {}
    if not isinstance(editor, dict):
        fail(errors, "culture_editor must be an object")
        return set(), {}
    selection = editor.get("selection")
    if not isinstance(selection, dict) or selection.get("mode") != "dynamic_daily":
        fail(errors, "culture_editor.selection.mode must be dynamic_daily")
    elif not isinstance(selection.get("max_cards"), int) or selection["max_cards"] < 1:
        fail(errors, "culture_editor.selection.max_cards must be a positive integer")
    topics = editor.get("topics")
    topic_limits: dict[str, int] = {}
    if not isinstance(topics, list) or not topics:
        fail(errors, "culture_editor.topics must be a non-empty list")
    else:
        for index, topic in enumerate(topics):
            prefix = f"culture_editor.topics[{index}]"
            if not isinstance(topic, dict) or not isinstance(topic.get("id"), str):
                fail(errors, f"{prefix}.id must be a string")
                continue
            topic_id = topic["id"]
            if topic_id in topic_limits:
                fail(errors, f"duplicate culture topic id: {topic_id}")
                continue
            target, maximum = topic.get("target_cards"), topic.get("max_cards")
            if not isinstance(target, int) or target < 0:
                fail(errors, f"{prefix}.target_cards must be a non-negative integer")
            if not isinstance(maximum, int) or maximum < 1:
                fail(errors, f"{prefix}.max_cards must be a positive integer")
            elif isinstance(target, int) and target > maximum:
                fail(errors, f"{prefix}.target_cards cannot exceed max_cards")
            if isinstance(maximum, int) and maximum > 0:
                topic_limits[topic_id] = maximum
    candidates = editor.get("candidates")
    candidate_ids: set[str] = set()
    if not isinstance(candidates, list) or not candidates:
        fail(errors, "culture_editor.candidates must be a non-empty list")
    else:
        for index, candidate in enumerate(candidates):
            prefix = f"culture_editor.candidates[{index}]"
            if not isinstance(candidate, dict):
                fail(errors, f"{prefix} must be an object")
                continue
            candidate_id = candidate.get("id")
            if not isinstance(candidate_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}", candidate_id):
                fail(errors, f"{prefix}.id must be a stable lowercase slug")
            elif candidate_id in candidate_ids:
                fail(errors, f"duplicate culture candidate id: {candidate_id}")
            else:
                candidate_ids.add(candidate_id)
            if candidate.get("topic_id") not in topic_limits:
                fail(errors, f"{prefix}.topic_id must reference a culture topic")
            if not isinstance(candidate.get("title"), str) or not candidate["title"]:
                fail(errors, f"{prefix}.title must be non-empty")
            if not isinstance(candidate.get("editorial_rank"), int) or candidate["editorial_rank"] < 1:
                fail(errors, f"{prefix}.editorial_rank must be a positive integer")
            refs = candidate.get("trip_refs")
            if not isinstance(refs, list):
                fail(errors, f"{prefix}.trip_refs must be a list")
            else:
                for ref in refs:
                    if ref not in trip_ids:
                        fail(errors, f"{prefix}.trip_refs references unknown trip id: {ref}")
    history = editor.get("history", [])
    if not isinstance(history, list):
        fail(errors, "culture_editor.history must be a list")
    else:
        for index, record in enumerate(history):
            prefix = f"culture_editor.history[{index}]"
            if not isinstance(record, dict):
                fail(errors, f"{prefix} must be an object")
                continue
            if record.get("candidate_id") not in candidate_ids:
                fail(errors, f"{prefix}.candidate_id must reference a culture candidate")
            if record.get("topic_id") not in topic_limits:
                fail(errors, f"{prefix}.topic_id must reference a culture topic")
            if not valid_date(record.get("date")):
                fail(errors, f"{prefix}.date must use YYYY-MM-DD")
            if record.get("exposure") not in {"preview", "notified"}:
                fail(errors, f"{prefix}.exposure must be preview or notified")
            if not isinstance(record.get("counts_toward_quota"), bool):
                fail(errors, f"{prefix}.counts_toward_quota must be boolean")
    return candidate_ids, topic_limits


def validate(value: object, program_path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["program must be a JSON object"]
    if value.get("schema") != "trip-buddy-program/v1":
        fail(errors, "schema must be trip-buddy-program/v1")
    trip_ref = value.get("trip_ref")
    if not isinstance(trip_ref, str) or not trip_ref:
        fail(errors, "trip_ref must be a non-empty relative path")
    elif Path(trip_ref).is_absolute() or not (program_path.parent / trip_ref).resolve().is_file():
        fail(errors, "trip_ref must resolve to an existing trip.json")
    trip_ids: set[str] = set()
    if isinstance(trip_ref, str) and trip_ref and not Path(trip_ref).is_absolute():
        try:
            trip_ids = trip_record_ids((program_path.parent / trip_ref).resolve())
        except (OSError, json.JSONDecodeError, AttributeError):
            fail(errors, "trip_ref is not readable canonical trip.json")
    if not isinstance(value.get("timezone"), str) or not value["timezone"]:
        fail(errors, "timezone must be non-empty")
    if not isinstance(value.get("language"), str) or not value["language"]:
        fail(errors, "language must be non-empty")
    candidate_ids, topic_limits = validate_culture_editor(value.get("culture_editor"), trip_ids, errors)
    delivery = value.get("delivery")
    if not isinstance(delivery, dict):
        fail(errors, "delivery must be an object")
    elif delivery.get("mode") not in DELIVERY_MODES:
        fail(errors, "delivery.mode must be manual, scheduled, or alert_only")
    validate_timing(delivery, errors)
    for key in SECRET_KEYS:
        if key in value or (isinstance(delivery, dict) and key in delivery):
            fail(errors, f"private identifier or credential is not allowed: {key}")
    items = value.get("items")
    if not isinstance(items, list):
        return errors + ["items must be a list"]
    ids: set[str] = set()
    for index, item in enumerate(items):
        prefix = f"items[{index}]"
        if not isinstance(item, dict):
            fail(errors, f"{prefix} must be an object")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}", item_id):
            fail(errors, f"{prefix}.id must be a stable lowercase slug")
        elif item_id in ids:
            fail(errors, f"duplicate item id: {item_id}")
        else:
            ids.add(item_id)
        if item.get("kind") not in KINDS:
            fail(errors, f"{prefix}.kind is invalid")
        if item.get("phase") not in PHASES:
            fail(errors, f"{prefix}.phase is invalid")
        if item.get("status") not in STATUSES:
            fail(errors, f"{prefix}.status is invalid")
        trigger = item.get("trigger")
        if not isinstance(trigger, dict) or trigger.get("type") not in {"scheduled", "event"}:
            fail(errors, f"{prefix}.trigger must declare scheduled or event")
        elif trigger["type"] == "scheduled" and not valid_date(trigger.get("date")):
            fail(errors, f"{prefix}.trigger.date must use YYYY-MM-DD")
        refs = item.get("trip_refs")
        if not isinstance(refs, list):
            fail(errors, f"{prefix}.trip_refs must be a list")
        else:
            for ref in refs:
                if ref not in trip_ids:
                    fail(errors, f"{prefix}.trip_refs references unknown trip id: {ref}")
        if item.get("kind") == "disruption" and item.get("priority") == "alert":
            for field in ("source_url", "checked_at", "valid_until", "impact", "fallback"):
                if not item.get(field):
                    fail(errors, f"{prefix} alert disruption requires {field}")
        if item.get("status") == "sending" and delivery and delivery.get("mode") == "manual":
            fail(errors, f"{prefix} cannot be sending while delivery.mode is manual")
        selection = item.get("selection")
        if selection is not None:
            if item.get("kind") != "culture" or not isinstance(selection, dict):
                fail(errors, f"{prefix}.selection is only valid for a culture item")
            else:
                if selection.get("candidate_id") not in candidate_ids:
                    fail(errors, f"{prefix}.selection.candidate_id must reference a culture candidate")
                if selection.get("topic_id") not in topic_limits:
                    fail(errors, f"{prefix}.selection.topic_id must reference a culture topic")
                if not isinstance(selection.get("selected_at"), str) or not selection["selected_at"]:
                    fail(errors, f"{prefix}.selection.selected_at must be non-empty")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_program.py path/to/program.json")
        return 2
    path = Path(sys.argv[1]).resolve()
    try:
        program = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: program does not exist: {path}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON: {exc}")
        return 1
    errors = validate(program, path)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("Trip Buddy program is valid!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
