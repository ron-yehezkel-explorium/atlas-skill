"""Shared dataclasses and utility functions for the team timeline pipeline."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class Ticket:
    """A locally-tracked ticket with editable planning fields."""
    key: str
    title: str
    assignee: str
    topic: str
    status: str
    parent_epic: str
    labels: list[str]
    estimation: int
    last_synced: str
    group_status: str
    group_assignee: str


@dataclass
class TopicRule:
    """Topic metadata for gantt styling (colour, legend); ids match per-ticket ``topic`` in markdown."""
    topic: str
    label: str
    color: str


@dataclass
class CapacityEvent:
    """A non-working or capacity-block event (holiday, on-call, OOO)."""
    start_date: date
    duration_days: int
    label: str


@dataclass
class CapacityConfig:
    """Full capacity/calendar configuration for the team."""
    timezone: str
    working_days: list[str]
    weekend_days: list[str]
    changeover: str
    representation_label: str
    representation_duration_days: int
    current_oncall: str
    rotation_order: list[str]
    global_non_working_days: list[CapacityEvent] = field(default_factory=list)
    per_person_capacity_events: dict[str, list[CapacityEvent]] = field(default_factory=dict)


@dataclass
class JiraIssue:
    """Raw issue fetched from Jira (pre-merge)."""
    key: str
    title: str
    assignee: str | None
    status: str
    issue_type: str
    labels: list[str]


@dataclass
class Segment:
    """A rendered gantt bar segment."""
    label: str
    task_id: str
    section: str
    start: date
    duration_days: int
    order_index: int


# ── Lookup tables ─────────────────────────────────────────────────────────────

NAME_TO_WEEKDAY: dict[str, int] = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


# ── Shared utilities ──────────────────────────────────────────────────────────

def json_dumps(data: Any) -> str:
    """Deterministic JSON serialisation for CLI output."""
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


def now_local(tz_name: str) -> datetime:
    """Current datetime in the given timezone."""
    return datetime.now(ZoneInfo(tz_name))


def now_iso(tz_name: str) -> str:
    """Current ISO-8601 timestamp in the given timezone."""
    return now_local(tz_name).isoformat(timespec="seconds")


def normalize_whitespace(value: str) -> str:
    """Collapse runs of whitespace to a single space."""
    return re.sub(r"\s+", " ", value.strip())


def sanitize_label(value: str) -> str:
    """Make a string safe for Mermaid gantt labels."""
    value = value.replace(":", " - ").replace("`", "")
    value = value.replace("\n", " ").replace("\r", " ")
    return normalize_whitespace(value)


def truncate_gantt_label(label: str, max_chars: int) -> str:
    """Shorten a label so it fits the gantt bar; Mermaid otherwise renders text outside the bar."""
    if max_chars < 3:
        max_chars = 3
    if len(label) <= max_chars:
        return label
    cut = max_chars - 1
    return label[:cut].rstrip() + "…"


_PART_SUFFIX = re.compile(r"^(.*) \(part (\d+)/(\d+)\)$")


def truncate_gantt_label_with_part(label: str, max_chars: int) -> str:
    """Like ``truncate_gantt_label`` but keeps a trailing `` (part i/n)`` suffix when present."""
    m = _PART_SUFFIX.match(label)
    if not m:
        return truncate_gantt_label(label, max_chars)
    base, pi, pt = m.group(1), m.group(2), m.group(3)
    suffix = f" (part {pi}/{pt})"
    if len(suffix) >= max_chars:
        return truncate_gantt_label(label, max_chars)
    base_budget = max(3, max_chars - len(suffix))
    return truncate_gantt_label(base, base_budget) + suffix


def parse_date(value: str) -> date:
    """Parse an ISO-8601 date string."""
    return date.fromisoformat(value.strip())
