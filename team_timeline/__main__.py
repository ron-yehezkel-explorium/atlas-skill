"""CLI entrypoint for the team timeline pipeline.

Usage (from atlas-skill root):
    python3 -m team_timeline build   --tickets reference/team-timeline-tickets.md --output-root output
    python3 -m team_timeline build   ... --local-only   # no Jira; does not rewrite tickets file
    python3 -m team_timeline preflight --tickets reference/team-timeline-tickets.md --output-root output
    # preflight writes output/preflight-smoke.png (first weekly strip from latest .mmd)
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import time
from datetime import timedelta
from pathlib import Path

from .calendar import clip_segments_to_exclusive_end, schedule, trim_capacity_segments_after_chart_end
from .config import (
    DEFAULT_JIRA_TYPE,
    DEFAULT_VIEW_DAYS,
    JIRA,
    MAIN_ASSIGNEES,
    OUTPUT,
    STATUSES,
    TIMEZONE,
    capacity_config,
    default_type_rules_with_capacity,
)
from .jira_fetch import (
    fetch_all_jira,
    fetch_jira_type_labels_from_createmeta,
    filter_issues,
    ordered_jira_type_labels,
)
from .models import json_dumps, now_local, parse_date
from .render import first_mermaid_diagram_for_smoke, latest_mmd, render, resolve_render_type_rules
from .state import (
    parse_tickets_markdown,
    render_tickets_markdown,
    sections_from_flat_tickets,
)
from .sync import merge_tickets


def run_preflight(args: argparse.Namespace) -> int:
    """Validate config and smoke-render the latest .mmd file."""
    import subprocess

    started = time.time()
    tickets_path = Path(args.tickets)
    output_root = Path(args.output_root)

    parse_started = time.time()
    tickets = parse_tickets_markdown(tickets_path)
    ordered = sorted({t.jira_type for t in tickets}) or [DEFAULT_JIRA_TYPE]
    rules = default_type_rules_with_capacity(ordered)
    config = capacity_config()
    parse_ms = int((time.time() - parse_started) * 1000)

    render_ms = 0
    rendered = False
    smoke_png: Path | None = None
    mmd = Path(args.latest_mmd) if args.latest_mmd else latest_mmd(output_root)
    if mmd and mmd.exists():
        output_root.mkdir(parents=True, exist_ok=True)
        smoke_png = output_root / "preflight-smoke.png"
        with tempfile.TemporaryDirectory() as tmp:
            smoke_mmd = Path(tmp) / "preflight.mmd"
            smoke_mmd.write_text(first_mermaid_diagram_for_smoke(mmd))
            started_render = time.time()
            subprocess.run(
                OUTPUT["mermaid_command"] + [
                    "-i", str(smoke_mmd), "-o", str(smoke_png),
                    "-e", "png",
                    "-b", OUTPUT["png_background"],
                    "-w", str(OUTPUT["png_width"]),
                    "-s", str(OUTPUT["png_scale"]),
                ],
                check=True, capture_output=True, text=True,
            )
            render_ms = int((time.time() - started_render) * 1000)
            rendered = smoke_png.exists()

    print(json_dumps({
        "ok": True,
        "tickets_count": len(tickets),
        "types_count": len(rules),
        "render_smoke_succeeded": rendered,
        "smoke_png": str(smoke_png) if smoke_png else None,
        "latest_mmd": mmd.name if mmd else None,
        "working_days": config.working_days,
        "weekend_days": config.weekend_days,
        "parse_ms": parse_ms,
        "render_ms": render_ms,
        "total_ms": int((time.time() - started) * 1000),
    }))
    return 0


def _jira_stats_stub() -> dict[str, int]:
    return {"jira_calls": 0, "jira_pages": 0, "enrichment_calls": 0, "jira_fetch_ms": 0}


def _distinct_jira_types_from_sections(sections: dict[str, dict[str, list]]) -> list[str]:
    """Type labels present on merged tickets only (matches bars and legend)."""
    found: set[str] = set()
    for status in STATUSES:
        for lane in MAIN_ASSIGNEES:
            for ticket in sections[status][lane]:
                found.add(ticket.jira_type)
    return sorted(found) or [DEFAULT_JIRA_TYPE]


def _merge_stats_from_sections(sections: dict) -> dict[str, int]:
    return {
        "synced_in_progress": sum(len(v) for v in sections["In Progress"].values()),
        "synced_to_do": sum(len(v) for v in sections["To Do"].values()),
        "new_tickets": 0,
        "removed_tickets": 0,
        "auto_estimation_count": 0,
    }


def run_build(args: argparse.Namespace) -> int:
    """Full pipeline: fetch Jira, merge, schedule, render (or local-only schedule + render)."""
    started = time.time()
    tickets_path = Path(args.tickets)
    output_root = Path(args.output_root)

    read_started = time.time()
    existing = parse_tickets_markdown(tickets_path)
    config = capacity_config()
    local_read_ms = int((time.time() - read_started) * 1000)

    if args.local_only:
        jira_stats = _jira_stats_stub()
        merge_started = time.time()
        sections = sections_from_flat_tickets(existing)
        merge_stats = _merge_stats_from_sections(sections)
        merge_ms = int((time.time() - merge_started) * 1000)
        flat_types = sorted({t.jira_type for t in existing}) or [DEFAULT_JIRA_TYPE]
        # Local-only: palette follows Type values present in the tickets file (no createmeta).
        config_rules = default_type_rules_with_capacity(flat_types)
    else:
        issues_by_status, jira_stats = fetch_all_jira()
        filtered = filter_issues(issues_by_status)

        merge_started = time.time()
        sections, merge_stats = merge_tickets(existing, filtered)
        merge_ms = int((time.time() - merge_started) * 1000)
        if JIRA.get("use_createmeta_for_type_order"):
            meta = fetch_jira_type_labels_from_createmeta()
            type_label_order = ordered_jira_type_labels(filtered, meta)
        else:
            # Only Jira Type values on allowlisted tickets — no legacy createmeta-only option names.
            type_label_order = _distinct_jira_types_from_sections(sections)
        config_rules = default_type_rules_with_capacity(type_label_order)

    window_start = parse_date(args.window_start) if args.window_start else now_local(TIMEZONE).date()
    oncall_horizon = window_start + timedelta(days=DEFAULT_VIEW_DAYS)
    segments = schedule(sections, config, window_start, oncall_horizon)

    # Exclusive end of the full work schedule (In Progress / To Do only for horizon).
    work_segments = [
        seg for seg in segments
        if seg.section in MAIN_ASSIGNEES and not seg.task_id.startswith("capacity_")
    ]
    if work_segments:
        natural_exclusive_end = max(
            seg.start + timedelta(days=seg.duration_days) for seg in work_segments
        )
    elif segments:
        natural_exclusive_end = max(
            seg.start + timedelta(days=seg.duration_days) for seg in segments
        )
    else:
        natural_exclusive_end = oncall_horizon

    # Drop trailing on-call/capacity after the last ticket (uses full schedule end).
    segments = trim_capacity_segments_after_chart_end(segments, natural_exclusive_end)

    # Visible chart: default max DEFAULT_VIEW_DAYS calendar days from window_start; full schedule
    # only with --full-horizon or an explicit --window-end (inclusive last day).
    if args.window_end:
        chart_exclusive_end = parse_date(args.window_end) + timedelta(days=1)
    elif args.full_horizon:
        chart_exclusive_end = natural_exclusive_end
    else:
        cap_exclusive = window_start + timedelta(days=DEFAULT_VIEW_DAYS)
        chart_exclusive_end = min(natural_exclusive_end, cap_exclusive)

    view_capped = natural_exclusive_end > chart_exclusive_end
    segments = clip_segments_to_exclusive_end(segments, chart_exclusive_end)

    display_rules = resolve_render_type_rules(config_rules, config_rules, segments)
    if not args.local_only:
        tickets_path.write_text(render_tickets_markdown(sections))

    if chart_exclusive_end <= window_start:
        window_end_inclusive = window_start
    else:
        window_end_inclusive = chart_exclusive_end - timedelta(days=1)

    stamp = now_local(TIMEZONE).strftime("%Y%m%d-%H%M%S")
    output_dir = output_root / f"{OUTPUT['folder_prefix']}-{stamp}"

    result = render(
        segments, display_rules, config, output_dir, window_start, window_end_inclusive,
        jira_stats, merge_stats, local_read_ms, merge_ms,
    )
    result["canonical_updated"] = not args.local_only
    result["local_only"] = bool(args.local_only)
    result["natural_work_end_exclusive"] = natural_exclusive_end.isoformat()
    result["view_capped"] = view_capped
    result["total_ms"] = int((time.time() - started) * 1000)
    print(json_dumps(result))
    return 0


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Team timeline pipeline")
    sub = p.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("preflight", help="Validate config and smoke-render latest .mmd")
    pre.add_argument("--tickets", required=True, help="Path to team-timeline-tickets.md")
    pre.add_argument("--output-root", required=True, help="Output root directory")
    pre.add_argument("--latest-mmd", help="Override path to .mmd file for smoke render")

    build = sub.add_parser("build", help="Full Jira sync + render")
    build.add_argument("--tickets", required=True, help="Path to team-timeline-tickets.md")
    build.add_argument("--output-root", required=True, help="Output root directory")
    build.add_argument(
        "--local-only",
        action="store_true",
        help="Skip Jira (no API calls); use tickets file as-is; do not rewrite the canonical markdown.",
    )
    build.add_argument("--window-start", help="Gantt start date YYYY-MM-DD (default: today)")
    build.add_argument(
        "--window-end",
        help="Inclusive last day of the chart (YYYY-MM-DD); overrides the default 30-day cap",
    )
    build.add_argument(
        "--full-horizon",
        action="store_true",
        help="Show the full schedule to the last task (overrides the default 30-day cap)",
    )

    return p


def main() -> int:
    args = _parser().parse_args()
    if args.command == "preflight":
        return run_preflight(args)
    if args.command == "build":
        return run_build(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
