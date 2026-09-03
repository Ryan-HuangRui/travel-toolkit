#!/usr/bin/env python3
"""Select one culture candidate from a Trip Buddy programme without prewriting it."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path


def slot_for(program: dict, selected_date: str) -> dict:
    for item in program["items"]:
        if item.get("kind") == "culture" and item.get("trigger", {}).get("date") == selected_date:
            return item
    raise ValueError(f"no culture slot is configured for {selected_date}")


def trip_ids(program: dict, program_path: Path) -> set[str]:
    trip_path = (program_path.parent / program["trip_ref"]).resolve()
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    ids: set[str] = set()
    for collection in ("constraints", "places", "decisions", "reservations", "candidates", "tasks", "budget", "sources"):
        ids.update(record["id"] for record in trip.get(collection, []) if isinstance(record, dict) and isinstance(record.get("id"), str))
    for day in trip.get("days", []):
        ids.update(item["id"] for item in day.get("items", []) if isinstance(item, dict) and isinstance(item.get("id"), str))
    return ids


def count_history(program: dict, ignore_preview_history: bool = False) -> tuple[dict[str, int], set[str], list[str]]:
    editor = program["culture_editor"]
    counts: dict[str, int] = {}
    used: set[str] = set()
    recent: list[tuple[str, str]] = []
    for record in editor.get("history", []):
        if ignore_preview_history and record["exposure"] == "preview":
            continue
        if record["exposure"] == "notified" or record["counts_toward_quota"]:
            counts[record["topic_id"]] = counts.get(record["topic_id"], 0) + 1
            used.add(record["candidate_id"])
            recent.append((record["date"], record["topic_id"]))
    for item in program["items"]:
        if item.get("kind") != "culture" or item.get("status") != "notified":
            continue
        selection = item.get("selection", {})
        candidate_id, topic_id = selection.get("candidate_id"), selection.get("topic_id")
        if candidate_id and topic_id:
            counts[topic_id] = counts.get(topic_id, 0) + 1
            used.add(candidate_id)
            recent.append((item.get("trigger", {}).get("date", ""), topic_id))
    recent.sort()
    return counts, used, [topic for _, topic in recent]


def choose(program: dict, program_path: Path, selected_date: str, ignore_preview_history: bool = False) -> dict:
    slot = slot_for(program, selected_date)
    if slot.get("selection"):
        return {"selection": slot["selection"], "already_selected": True}
    editor = program["culture_editor"]
    limits = {topic["id"]: topic["max_cards"] for topic in editor["topics"]}
    counts, used, recent = count_history(program, ignore_preview_history)
    used_cards = sum(counts.values())
    if used_cards >= editor["selection"]["max_cards"]:
        raise ValueError("culture programme has reached its max_cards limit")
    avoid = editor["selection"].get("avoid_recent_topic_cards", 0)
    blocked_topics = set(recent[-avoid:]) if avoid else set()
    current_trip_ids = trip_ids(program, program_path)
    eligible = [
        candidate for candidate in editor["candidates"]
        if candidate["id"] not in used
        and counts.get(candidate["topic_id"], 0) < limits[candidate["topic_id"]]
        and all(ref in current_trip_ids for ref in candidate["trip_refs"])
    ]
    if not eligible:
        raise ValueError("no eligible culture candidate remains")
    non_repeating = [candidate for candidate in eligible if candidate["topic_id"] not in blocked_topics]
    winner = min(non_repeating or eligible, key=lambda candidate: (candidate["editorial_rank"], candidate["id"]))
    return {
        "selection": {
            "candidate_id": winner["id"],
            "topic_id": winner["topic_id"],
            "selected_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        },
        "title": winner["title"],
        "remaining_slots": sum(
            1 for item in program["items"]
            if item.get("kind") == "culture"
            and item.get("trigger", {}).get("date", "") >= selected_date
            and item.get("status") == "planned"
            and not item.get("selection")
        ),
        "topic_cards_used": counts.get(winner["topic_id"], 0),
        "topic_cards_cap": limits[winner["topic_id"]],
        "already_selected": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("program")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--ignore-preview-history", action="store_true", help="simulate a first run without prior preview cards")
    args = parser.parse_args()
    selected_date = date.fromisoformat(args.date).isoformat()
    path = Path(args.program).resolve()
    program = json.loads(path.read_text(encoding="utf-8"))
    result = choose(program, path, selected_date, args.ignore_preview_history)
    if args.apply and not result["already_selected"]:
        slot_for(program, selected_date)["selection"] = result["selection"]
        path.write_text(json.dumps(program, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
