#!/usr/bin/env python3
"""Render Markdown and CSV views from a canonical trip.json."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def md(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def labels(language: str) -> dict[str, str]:
    if language.lower().startswith("zh"):
        return {
            "generated": "生成信息",
            "summary": "行程概览",
            "date": "日期",
            "base": "住宿地/基地",
            "plan": "安排",
            "status": "状态",
            "time": "时间",
            "place": "地点",
            "fallback": "备选",
            "confirmed": "已确认预订",
            "open_tasks": "待办事项",
            "constraints": "约束",
            "decisions": "决策",
            "candidates": "候选方案",
            "reservations": "预订",
            "tasks": "任务",
            "notes": "备注",
            "sources": "来源",
            "freshness": "新鲜度",
            "checked": "查询时间",
            "title": "标题",
            "category": "类别",
            "next_action": "下一步",
            "discoveries": "当地活动与特色",
            "confidence": "日期可信度",
            "route_fit": "动线匹配",
            "booking": "预约建议",
            "date_fit": "日期匹配",
            "date_flexibility": "日期弹性",
            "planning_phase": "规划阶段",
            "city_windows": "城市安排",
            "adjustment_options": "可选日期与城市安排",
            "proposed_window": "建议日期",
            "current_window": "当前城市安排",
            "impact": "影响",
            "decision": "待确认",
        }
    return {
        "generated": "Generation",
        "summary": "Trip summary",
        "date": "Date",
        "base": "Base",
        "plan": "Plan",
        "status": "Status",
        "time": "Time",
        "place": "Place",
        "fallback": "Fallback",
        "confirmed": "Confirmed reservations",
        "open_tasks": "Open tasks",
        "constraints": "Constraints",
        "decisions": "Decisions",
        "candidates": "Candidates",
        "reservations": "Reservations",
        "tasks": "Tasks",
        "notes": "Notes",
        "sources": "Sources",
        "freshness": "Freshness",
        "checked": "Checked at",
        "title": "Title",
        "category": "Category",
        "next_action": "Next action",
        "discoveries": "Local events and distinctive experiences",
        "confidence": "Date confidence",
        "route_fit": "Route fit",
        "booking": "Booking",
        "date_fit": "Date fit",
        "date_flexibility": "Date flexibility",
        "planning_phase": "Planning phase",
        "city_windows": "City scheduling",
        "adjustment_options": "Optional date and city scheduling",
        "proposed_window": "Proposed dates",
        "current_window": "Current city plan",
        "impact": "Impact",
        "decision": "Decision needed",
    }


def table(headers: list[str], rows: list[list[Any]]) -> str:
    output = ["| " + " | ".join(md(header) for header in headers) + " |"]
    output.append("|" + "|".join("---" for _ in headers) + "|")
    if rows:
        output.extend("| " + " | ".join(md(cell) for cell in row) + " |" for row in rows)
    else:
        output.append("| " + " | ".join("-" for _ in headers) + " |")
    return "\n".join(output)


def date_window(record: dict[str, Any], start_key: str = "start_date", end_key: str = "end_date") -> str:
    value = record.get(start_key, "")
    if record.get(end_key) and record.get(end_key) != value:
        value = f"{value} - {record[end_key]}" if value else record[end_key]
    return value


def stay_window_text(place: dict[str, Any]) -> str:
    stay_window = place.get("stay_window")
    if not isinstance(stay_window, dict):
        return "unassigned"
    status = stay_window.get("status", "unassigned")
    if status == "unassigned":
        return status
    window = date_window(stay_window)
    return f"{status}: {window}" if window else status


def render_bundle(trip_path: Path) -> list[Path]:
    trip_path = resolve_trip_path(trip_path)
    with trip_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    script_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(script_dir))
    from validate_trip import validate_bundle  # pylint: disable=import-outside-toplevel

    errors, warnings = validate_bundle(data)
    if errors:
        raise ValueError("cannot render invalid trip.json: " + "; ".join(errors))

    bundle_dir = trip_path.parent
    trip = data["trip"]
    language = str(trip.get("language", "en"))
    text = labels(language)
    places = {record.get("id"): record for record in data.get("places", []) if isinstance(record, dict)}
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    revision = data.get("revision", 0)
    marker = f"trip.json revision {revision}; rendered {generated_at}"

    itinerary: list[str] = [f"# {trip['title']}", "", f"> {text['generated']}: {marker}", ""]
    flexibility = trip.get("date_flexibility", {})
    flexibility_summary = flexibility.get("status", "")
    if flexibility_summary:
        flexibility_summary += f" (-{flexibility.get('days_before', 0)}/+{flexibility.get('days_after', 0)} days)"
    itinerary.extend([
        f"## {text['summary']}",
        "",
        table(
            [text["date"], text["plan"]],
            [[f"{trip['start_date']} - {trip['end_date']}", f"{trip['timezone']} · {trip['currency']} · {text['planning_phase']}: {trip.get('planning_phase', '-')} · {text['date_flexibility']}: {flexibility_summary or '-'}"]],
        ),
        "",
    ])
    for day in data.get("days", []):
        base = places.get(day.get("base_place_id"), {}).get("name", day.get("base_place_id", ""))
        heading = f"## {day.get('date', '')}"
        if day.get("summary"):
            heading += f" — {day['summary']}"
        itinerary.extend([heading, ""])
        if base:
            itinerary.extend([f"**{text['base']}:** {base}", ""])
        rows: list[list[Any]] = []
        for item in day.get("items", []):
            time_range = item.get("start_time", "")
            if item.get("end_time"):
                time_range = f"{time_range}-{item['end_time']}" if time_range else item["end_time"]
            place = places.get(item.get("place_id"), {}).get("name", item.get("place_id", ""))
            plan = item.get("title", "")
            if item.get("notes"):
                plan += f" — {item['notes']}"
            if item.get("fallback"):
                plan += f" ({text['fallback']}: {item['fallback']})"
            rows.append([time_range, plan, place, item.get("status", "")])
        itinerary.extend([table([text["time"], text["plan"], text["place"], text["status"]], rows), ""])

    discoveries = [
        record
        for record in data.get("candidates", [])
        if record.get("category") in DISCOVERY_CATEGORIES and record.get("status") != "rejected"
    ]
    if discoveries:
        discovery_rows = []
        for record in discoveries:
            discovery_window = date_window(record)
            if record.get("start_time"):
                time_window = record["start_time"]
                if record.get("end_time"):
                    time_window += f"-{record['end_time']}"
                discovery_window = f"{discovery_window} {time_window}".strip()
            place = places.get(record.get("place_id"), {}).get("name", record.get("place_id", ""))
            title = record.get("title", "")
            if record.get("notes"):
                title += f" — {record['notes']}"
            discovery_rows.append([
                record.get("category", ""),
                title,
                discovery_window,
                place,
                record.get("date_fit", ""),
                record.get("date_confidence", ""),
                record.get("route_fit", ""),
                record.get("booking_timing", ""),
            ])
        itinerary.extend([f"## {text['discoveries']}", ""])
        itinerary.extend([
            table(
                [text["category"], text["title"], text["date"], text["place"], text["date_fit"], text["confidence"], text["route_fit"], text["booking"]],
                discovery_rows,
            ),
            "",
        ])

    adjustment_rows = []
    for record in discoveries:
        adjustment = record.get("date_adjustment")
        if not isinstance(adjustment, dict):
            continue
        proposed_window = date_window(adjustment, "proposed_start_date", "proposed_end_date")
        adjustment_rows.append([
            record.get("title", ""),
            date_window(record),
            record.get("date_fit", ""),
            stay_window_text(places.get(record.get("place_id"), {})),
            proposed_window,
            adjustment.get("impact_summary", ""),
            adjustment.get("decision_prompt", ""),
        ])
    if adjustment_rows:
        itinerary.extend([f"## {text['adjustment_options']}", ""])
        itinerary.extend([
            table(
                [text["title"], text["date"], text["date_fit"], text["current_window"], text["proposed_window"], text["impact"], text["decision"]],
                adjustment_rows,
            ),
            "",
        ])

    confirmed = [record for record in data.get("reservations", []) if record.get("status") in {"confirmed", "booked", "completed"}]
    itinerary.extend([f"## {text['confirmed']}", ""])
    itinerary.extend([
        table(
            [text["category"], text["title"], text["date"], text["status"]],
            [[r.get("type", ""), r.get("title", ""), r.get("start", r.get("date", "")), r.get("status", "")] for r in confirmed],
        ),
        "",
    ])
    open_tasks = [record for record in data.get("tasks", []) if record.get("status") not in {"done", "dropped"}]
    itinerary.extend([f"## {text['open_tasks']}", ""])
    itinerary.extend([
        table(
            [text["title"], text["status"], text["date"], text["next_action"]],
            [[r.get("title", ""), r.get("status", ""), r.get("due_date", ""), r.get("next_action", "")] for r in open_tasks],
        ),
        "",
    ])
    if warnings:
        itinerary.extend(["## Validation warnings", "", *[f"- {warning}" for warning in warnings], ""])

    planning: list[str] = [f"# {trip['title']} — Planning", "", f"> {text['generated']}: {marker}", ""]
    city_rows = []
    for place in data.get("places", []):
        if not isinstance(place, dict) or "stay_window" not in place:
            continue
        stay_window = place.get("stay_window", {})
        city_rows.append([
            place.get("name", ""),
            stay_window.get("status", ""),
            date_window(stay_window),
            stay_window.get("days_before", ""),
            stay_window.get("days_after", ""),
        ])
    if city_rows:
        planning.extend([
            f"## {text['city_windows']}",
            "",
            table([text["place"], text["status"], text["date"], "Days before", "Days after"], city_rows),
            "",
        ])
    sections = [
        (text["constraints"], data.get("constraints", []), [text["title"], "Type", "Priority", text["notes"]], lambda r: [r.get("title", r.get("value", "")), r.get("type", ""), r.get("priority", ""), r.get("notes", "")]),
        (text["decisions"], data.get("decisions", []), [text["title"], text["status"], text["notes"]], lambda r: [r.get("title", ""), r.get("status", ""), r.get("reason", "")]),
        (text["candidates"], data.get("candidates", []), [text["category"], text["title"], text["date"], text["date_fit"], text["confidence"], text["route_fit"], text["status"], text["notes"]], lambda r: [r.get("category", ""), r.get("title", ""), r.get("start_date", ""), r.get("date_fit", ""), r.get("date_confidence", ""), r.get("route_fit", ""), r.get("status", ""), r.get("notes", "")]),
        (text["reservations"], data.get("reservations", []), [text["category"], text["title"], text["status"], text["notes"]], lambda r: [r.get("type", ""), r.get("title", ""), r.get("status", ""), r.get("notes", "")]),
        (text["tasks"], data.get("tasks", []), [text["title"], text["status"], text["date"], text["next_action"]], lambda r: [r.get("title", ""), r.get("status", ""), r.get("due_date", ""), r.get("next_action", "")]),
    ]
    for heading, records, headers, row_builder in sections:
        planning.extend([f"## {heading}", "", table(headers, [row_builder(record) for record in records]), ""])

    itinerary_path = bundle_dir / "itinerary.md"
    planning_path = bundle_dir / "planning.md"
    sources_path = bundle_dir / "sources.md"
    budget_path = bundle_dir / "budget.csv"
    itinerary_path.write_text("\n".join(itinerary).rstrip() + "\n", encoding="utf-8")
    planning_path.write_text("\n".join(planning).rstrip() + "\n", encoding="utf-8")

    source_rows = []
    for source in data.get("sources", []):
        title = source.get("title", "")
        if source.get("url"):
            title = f"[{title}]({source['url']})"
        source_rows.append([title, source.get("type", ""), source.get("checked_at", ""), source.get("freshness", ""), source.get("notes", "")])
    sources_content = "\n".join([
        f"# {trip['title']} — {text['sources']}",
        "",
        f"> {text['generated']}: {marker}",
        "",
        table([text["title"], "Type", text["checked"], text["freshness"], text["notes"]], source_rows),
        "",
    ])
    sources_path.write_text(sources_content, encoding="utf-8")

    with budget_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "category", "title", "date", "currency", "amount", "status", "related_id", "notes"])
        for record in data.get("budget", []):
            writer.writerow([
                record.get("id", ""),
                record.get("category", ""),
                record.get("title", ""),
                record.get("date", ""),
                record.get("currency", ""),
                record.get("amount", ""),
                record.get("status", ""),
                record.get("related_id", ""),
                record.get("notes", ""),
            ])
    return [itinerary_path, planning_path, budget_path, sources_path]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="trip.json or its bundle directory")
    args = parser.parse_args()
    try:
        outputs = render_bundle(args.path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
