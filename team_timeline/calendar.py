"""Date math, working-day allocation, on-call generation, and gantt scheduling."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta

from .config import GANTT_LANE_ASSIGNEES, MAIN_ASSIGNEES
from .models import (
    CapacityConfig, CapacityEvent, NAME_TO_WEEKDAY, Segment, Ticket,
    capacity_tooltip_text,
    parse_date,
    sanitize_label,
    ticket_bar_display_label,
    ticket_tooltip_text,
    type_id_from_jira_label,
)


# ── Working-day helpers ───────────────────────────────────────────────────────

def weekday_indexes(day_names: list[str]) -> set[int]:
    """Convert day name strings to weekday integers (Mon=0 … Sun=6)."""
    return {NAME_TO_WEEKDAY[name.lower()] for name in day_names}


def is_working_day(day: date, working_weekdays: set[int], excluded: set[date]) -> bool:
    return day.weekday() in working_weekdays and day not in excluded


def event_dates(event: CapacityEvent) -> list[date]:
    """Expand a CapacityEvent into individual dates."""
    start = parse_date(event.start_date) if isinstance(event.start_date, str) else event.start_date
    return [start + timedelta(days=i) for i in range(event.duration_days)]


def excluded_global_dates(config: CapacityConfig) -> set[date]:
    """Collect all globally excluded dates from the capacity config."""
    excluded: set[date] = set()
    for event in config.global_non_working_days:
        excluded.update(event_dates(event))
    return excluded


def blocked_dates(events: list[CapacityEvent]) -> set[date]:
    """Collect all dates covered by a list of capacity events."""
    blocked: set[date] = set()
    for event in events:
        blocked.update(event_dates(event))
    return blocked


def collapse_dates(days: list[date], working_weekdays: set[int], excluded: set[date]) -> list[tuple[date, int]]:
    """Compress a list of dates into (start, length) chunks of consecutive working days."""
    days = [d for d in days if is_working_day(d, working_weekdays, excluded)]
    if not days:
        return []
    chunks: list[tuple[date, int]] = []
    start = days[0]
    length = 1
    for prev, cur in zip(days, days[1:]):
        if cur == prev + timedelta(days=1):
            length += 1
        else:
            chunks.append((start, length))
            start = cur
            length = 1
    chunks.append((start, length))
    return chunks


def next_weekday_on_or_after(start: date, weekday: int) -> date:
    return start + timedelta(days=(weekday - start.weekday()) % 7)


def capacity_event_is_oncall(ev: CapacityEvent, config: CapacityConfig) -> bool:
    """True for generated on-call rotation blocks (matches ``representation_label``)."""
    return (ev.label or "").strip() == (config.representation_label or "").strip()


def _segment_sort_key(seg: Segment) -> tuple[date, str]:
    return (seg.start, seg.task_id)


def merge_lane_segment_order(
    ip_segs: list[Segment],
    oncall_segs: list[Segment],
    other_cap_segs: list[Segment],
    td_segs: list[Segment],
) -> list[Segment]:
    """Gantt row order: in-progress tickets, then on-call, then other capacity, then to-do.

    If there is no in-progress work, on-call leads (so it does not list above tickets that
    start after it). Calendar dates are unchanged; only ``order_index`` is reassigned.
    """
    ip_segs = sorted(ip_segs, key=_segment_sort_key)
    oncall_segs = sorted(oncall_segs, key=_segment_sort_key)
    other_cap_segs = sorted(other_cap_segs, key=_segment_sort_key)
    td_segs = sorted(td_segs, key=_segment_sort_key)
    if ip_segs:
        merged = ip_segs + oncall_segs + other_cap_segs + td_segs
    else:
        merged = oncall_segs + other_cap_segs + td_segs
    return [replace(seg, order_index=i) for i, seg in enumerate(merged, start=1)]


# ── On-call generation ────────────────────────────────────────────────────────

def generate_oncall_events(config: CapacityConfig, start: date, horizon: date) -> dict[str, list[CapacityEvent]]:
    """Generate on-call capacity events for each person within [start, horizon]."""
    events: dict[str, list[CapacityEvent]] = {person: [] for person in MAIN_ASSIGNEES}
    current_index = config.rotation_order.index(config.current_oncall)
    owner_index = (current_index + 1) % len(config.rotation_order)
    target_weekday = NAME_TO_WEEKDAY[config.changeover.split()[0].lower()]
    day = next_weekday_on_or_after(start, target_weekday)
    while day <= horizon:
        owner = config.rotation_order[owner_index]
        events[owner].append(CapacityEvent(
            start_date=day,
            duration_days=config.representation_duration_days,
            label=config.representation_label,
        ))
        owner_index = (owner_index + 1) % len(config.rotation_order)
        day += timedelta(days=7)
    return events


# ── Segment allocation ────────────────────────────────────────────────────────

def allocate_segments(
    start: date,
    effort: int,
    blocked: set[date],
    working_weekdays: set[int],
    excluded: set[date],
) -> tuple[list[tuple[date, int]], date]:
    """Allocate `effort` working days starting from `start`, skipping blocked/non-working days.

    Returns the list of (chunk_start, chunk_length) segments and the cursor
    position after the last allocated day.
    """
    current = start
    remaining = max(effort, 1)
    chunks: list[tuple[date, int]] = []
    chunk_start: date | None = None
    chunk_len = 0
    while remaining > 0:
        usable = is_working_day(current, working_weekdays, excluded) and current not in blocked
        if usable:
            if chunk_start is None:
                chunk_start = current
            chunk_len += 1
            remaining -= 1
        else:
            if chunk_start is not None:
                chunks.append((chunk_start, chunk_len))
                chunk_start = None
                chunk_len = 0
        current += timedelta(days=1)
    if chunk_start is not None:
        chunks.append((chunk_start, chunk_len))
    return chunks, current


def segment_label(base: str, total: int, index: int) -> str:
    """Label a segment when the same ticket or capacity block spans non-working gaps.

    Multiple rows in the gantt are one logical item; ``(part i/n)`` ties them together.
    """
    if total <= 1:
        return base
    return f"{base} (part {index}/{total})"


# ── Top-level scheduler ───────────────────────────────────────────────────────

def schedule(
    sections: dict[str, dict[str, list[Ticket]]],
    config: CapacityConfig,
    start: date,
    oncall_horizon: date,
) -> list[Segment]:
    """Schedule all tickets and capacity events into gantt Segments.

    On-call events are generated only up to `oncall_horizon` (near-term window).
    All work tickets in gantt-visible lanes are scheduled without a cutoff (see ``GANTT_EXCLUDE_LANES``).

    Lane **row order** (``order_index``): in-progress ticket chunks first, then on-call, then other
    capacity (PTO/holidays), then to-do tickets. If there is no in-progress ticket, on-call rows come
    first so on-call does not sit above unrelated to-dos. Calendar start dates and blocking are unchanged.
    """
    segments: list[Segment] = []
    working_weekdays = weekday_indexes(config.working_days)
    excluded = excluded_global_dates(config)
    oncall = generate_oncall_events(config, start, oncall_horizon)

    for lane in GANTT_LANE_ASSIGNEES:
        cursor = start
        events = (config.per_person_capacity_events.get(lane) or []) + (oncall.get(lane) or [])
        lane_blocked = blocked_dates(events)

        other_events = [e for e in events if not capacity_event_is_oncall(e, config)]
        oncall_events = [e for e in events if capacity_event_is_oncall(e, config)]
        other_cap_segs: list[Segment] = []
        oncall_segs: list[Segment] = []
        cap_order = 0

        for event in sorted(
            other_events,
            key=lambda e: parse_date(e.start_date) if isinstance(e.start_date, str) else e.start_date,
        ):
            cap_order += 1
            chunks = collapse_dates(event_dates(event), working_weekdays, excluded)
            for idx, (chunk_start, duration) in enumerate(chunks, start=1):
                cap_lbl = segment_label(event.label, len(chunks), idx)
                other_cap_segs.append(
                    Segment(
                        label=cap_lbl,
                        task_id=f"capacity_{lane}_{cap_order}_{idx}",
                        section=lane,
                        start=chunk_start,
                        duration_days=duration,
                        order_index=0,
                        tooltip=capacity_tooltip_text(lane, cap_lbl),
                        type_id="capacity",
                    )
                )

        for event in sorted(
            oncall_events,
            key=lambda e: parse_date(e.start_date) if isinstance(e.start_date, str) else e.start_date,
        ):
            cap_order += 1
            chunks = collapse_dates(event_dates(event), working_weekdays, excluded)
            for idx, (chunk_start, duration) in enumerate(chunks, start=1):
                cap_lbl = segment_label(event.label, len(chunks), idx)
                oncall_segs.append(
                    Segment(
                        label=cap_lbl,
                        task_id=f"capacity_{lane}_{cap_order}_{idx}",
                        section=lane,
                        start=chunk_start,
                        duration_days=duration,
                        order_index=0,
                        tooltip=capacity_tooltip_text(lane, cap_lbl),
                        type_id="capacity",
                    )
                )

        ip_segs: list[Segment] = []
        td_segs: list[Segment] = []
        ticket_order = 0

        for ticket in sections["In Progress"][lane]:
            ticket_order += 1
            tid = type_id_from_jira_label(ticket.jira_type)
            chunks, cursor = allocate_segments(
                cursor, ticket.estimation, lane_blocked, working_weekdays, excluded
            )
            for idx, (chunk_start, duration) in enumerate(chunks, start=1):
                short_lbl = ticket_bar_display_label(ticket)
                base_lbl = segment_label(short_lbl, len(chunks), idx)
                tip = ticket_tooltip_text(ticket)
                ip_segs.append(
                    Segment(
                        label=base_lbl,
                        task_id=f"{tid}_{ticket.key}_{ticket_order}_{idx}",
                        section=lane,
                        start=chunk_start,
                        duration_days=duration,
                        order_index=0,
                        tooltip=tip,
                        type_id=tid,
                    )
                )

        for ticket in sections["To Do"][lane]:
            ticket_order += 1
            tid = type_id_from_jira_label(ticket.jira_type)
            chunks, cursor = allocate_segments(
                cursor, ticket.estimation, lane_blocked, working_weekdays, excluded
            )
            for idx, (chunk_start, duration) in enumerate(chunks, start=1):
                short_lbl = ticket_bar_display_label(ticket)
                base_lbl = segment_label(short_lbl, len(chunks), idx)
                tip = ticket_tooltip_text(ticket)
                td_segs.append(
                    Segment(
                        label=base_lbl,
                        task_id=f"{tid}_{ticket.key}_{ticket_order}_{idx}",
                        section=lane,
                        start=chunk_start,
                        duration_days=duration,
                        order_index=0,
                        tooltip=tip,
                        type_id=tid,
                    )
                )

        segments.extend(
            merge_lane_segment_order(ip_segs, oncall_segs, other_cap_segs, td_segs)
        )

    return segments


def trim_capacity_segments_after_chart_end(
    segments: list[Segment],
    chart_end: date,
) -> list[Segment]:
    """Remove capacity/on-call (and PTO) bars that start on or after the chart end.

    ``chart_end`` is the exclusive end of the planning window — normally the
    exclusive end date of the last In Progress / To Do ticket. On-call slots are
    generated out to a near-term horizon, so without this the gantt time axis
    stretches past the last ticket to show a lone trailing on-call bar.
    """
    return [
        s
        for s in segments
        if not (s.task_id.startswith("capacity_") and s.start >= chart_end)
    ]


def clip_segments_to_exclusive_end(
    segments: list[Segment],
    chart_exclusive_end: date,
) -> list[Segment]:
    """Drop or truncate segments so no bar extends past ``chart_exclusive_end``.

    ``chart_exclusive_end`` is the first calendar day *after* the visible chart
    (same convention as ``seg.start + timedelta(days=seg.duration_days)``).
    """
    out: list[Segment] = []
    for seg in segments:
        if seg.start >= chart_exclusive_end:
            continue
        seg_exc = seg.start + timedelta(days=seg.duration_days)
        if seg_exc <= chart_exclusive_end:
            out.append(seg)
            continue
        new_dur = (chart_exclusive_end - seg.start).days
        if new_dur < 1:
            continue
        out.append(replace(seg, duration_days=new_dur))
    return out


def mermaid_weekend_directive(config: CapacityConfig) -> str | None:
    """Return the `weekend` line for Mermaid (`weekend friday` / `weekend saturday`), or None.

    When using `excludes weekends`, Mermaid needs this so Fri/Sat vs Sat/Sun matches the team.
    See ganttDb.js `isInvalidDate` (short names like `fri` do not match `dddd`).
    """
    w = tuple(sorted(config.weekend_days))
    if w == ("Friday", "Saturday"):
        return "friday"
    if w == ("Saturday", "Sunday"):
        return "saturday"
    return None


def mermaid_excludes(config: CapacityConfig) -> str:
    """Build the Mermaid `excludes` list: weekends keyword + explicit global holiday dates.

    For non-standard weekend sets (not Fri/Sat or Sat/Sun), lists full weekday names
    (e.g. `friday`, `saturday`) which match `isInvalidDate`.
    """
    parts: list[str] = []
    if mermaid_weekend_directive(config) is not None:
        parts.append("weekends")
    else:
        for name in config.weekend_days:
            parts.append(name.lower())
    for d in sorted(excluded_global_dates(config)):
        parts.append(d.isoformat())
    return ",".join(parts)


def mermaid_excludes_for_strip(
    config: CapacityConfig,
    strip_start: date,
    strip_exclusive_end: date,
) -> str:
    """Mermaid ``excludes`` for a Sun–Thu strip only: global holidays in that date range.

    The axis does not include Friday or Saturday, so the ``weekends`` keyword and
    ``weekend`` directive are omitted — non-working Fri/Sat are absent from the chart
    rather than greyed out.
    """
    parts: list[str] = []
    for d in sorted(excluded_global_dates(config)):
        if strip_start <= d < strip_exclusive_end:
            parts.append(d.isoformat())
    return ",".join(parts)


def mermaid_exclude_comments_for_strip(
    config: CapacityConfig,
    strip_start: date,
    strip_exclusive_end: date,
) -> list[str]:
    """``%%`` comments for holidays that fall inside this strip (for the .mmd source)."""
    lines = [
        "%% Grey columns: team holidays in this strip (Sun–Thu only; Fri/Sat not on axis).",
    ]
    for ev in config.global_non_working_days:
        for day in event_dates(ev):
            if strip_start <= day < strip_exclusive_end:
                safe = ev.label.replace("\\", "\\\\").replace("%%", "")
                lines.append(f"%% {day.isoformat()}: {safe}")
    return lines


def iter_dates_inclusive(start: date, end: date):
    """Yield each calendar day from start through end (inclusive)."""
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def non_working_days_in_window(
    config: CapacityConfig, window_start: date, window_end: date
) -> list[dict[str, str]]:
    """Team-wide non-working days in the view window (grey gantt columns).

    Sources: ``config.weekend_days`` (Mermaid ``excludes`` + scheduling) and
    ``config.global_non_working_days`` (team holidays). Per-person PTO is
    ``per_person_capacity_events`` — those affect scheduling and capacity bars only,
    not column shading.
    """
    weekend_ix = weekday_indexes(config.weekend_days)
    global_by_date: dict[date, str] = {}
    for ev in config.global_non_working_days:
        for day in event_dates(ev):
            global_by_date[day] = ev.label

    rows: list[dict[str, str]] = []
    for d in iter_dates_inclusive(window_start, window_end):
        if d in global_by_date:
            reason = global_by_date[d]
            if d.weekday() in weekend_ix:
                reason = f"{reason} (also weekend)"
            rows.append(
                {"date": d.isoformat(), "weekday": d.strftime("%A"), "reason": reason}
            )
        elif d.weekday() in weekend_ix:
            rows.append(
                {"date": d.isoformat(), "weekday": d.strftime("%A"), "reason": "Weekend"}
            )
    return rows


def mermaid_exclude_comments(config: CapacityConfig) -> list[str]:
    """%% comments documenting global holidays (shown in .mmd source, not on the PNG)."""
    lines = [
        "%% Grey columns: team-wide non-working (weekends + holidays below).",
    ]
    for ev in config.global_non_working_days:
        for day in event_dates(ev):
            safe = ev.label.replace("\\", "\\\\").replace("%%", "")
            lines.append(f"%% {day.isoformat()}: {safe}")
    return lines
