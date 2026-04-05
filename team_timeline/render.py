"""Mermaid gantt generation, PNG rendering, and metadata output."""

from __future__ import annotations

import subprocess
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .calendar import (
    mermaid_exclude_comments,
    mermaid_excludes,
    mermaid_weekend_directive,
    non_working_days_in_window,
)
from .config import (
    GANTT_AXIS_LR_PADDING,
    GANTT_BAR_HEIGHT,
    GANTT_FONT_SIZE,
    GANTT_TASK_TITLE_FONT_WEIGHT,
    GANTT_LABEL_CHAR_MARGIN,
    GANTT_LABEL_PX_PER_CHAR,
    LEGEND,
    MAIN_ASSIGNEES,
    ON_HOLD_GANTT_SECTION,
    OUTPUT,
)
from .models import CapacityConfig, Segment, TopicRule, truncate_gantt_label_with_part


def topics_referenced_by_segments(segments: list[Segment]) -> set[str]:
    """Topic ids used in gantt bar task ids (for CSS selectors and legend)."""
    out: set[str] = set()
    for seg in segments:
        tid = seg.task_id
        if tid.startswith("capacity_"):
            out.add("capacity")
        elif tid.startswith("on_hold_"):
            out.add("on_hold")
        else:
            mark = "_ATB-"
            if mark in tid:
                out.add(tid.split(mark, 1)[0])
    return out


def resolve_render_topic_rules(
    file_rules: list[TopicRule],
    config_rules: list[TopicRule],
    segments: list[Segment],
) -> list[TopicRule]:
    """Build ordered topic rules for Mermaid CSS + legend.

    Colours and legend order follow ``file_rules`` when present; any topic that
    appears in ``segments`` but is missing there is filled from ``config_rules``.
    """
    topics_used = topics_referenced_by_segments(segments)
    if not file_rules:
        file_rules = list(config_rules)
    seen: set[str] = set()
    out: list[TopicRule] = []
    for r in file_rules:
        if r.topic in topics_used:
            out.append(r)
            seen.add(r.topic)
    for r in config_rules:
        if r.topic in topics_used and r.topic not in seen:
            out.append(r)
            seen.add(r.topic)
    for t in sorted(topics_used - seen):
        out.append(TopicRule(topic=t, label=t.replace("_", " "), color="#9aa0a6"))
    return out


def build_theme_css(
    rules: list[TopicRule],
    *,
    tick_label_shift_px: float | None = None,
) -> str:
    """Generate inline CSS for topic-colour coding in the Mermaid gantt."""
    parts = [
        f'rect[id*="{rule.topic}_"] {{ fill: {rule.color}; stroke: {rule.color}; }}'
        for rule in rules
    ]
    # Ticks sit on day boundaries (midnight); shift by half a day-width to center on the column.
    if tick_label_shift_px is not None and tick_label_shift_px > 0:
        parts.append(
            f"g.grid g.tick text {{ transform: translateX({tick_label_shift_px:.3f}px); }}"
        )
    # Bold task titles (inside-bar and outside-bar label text; not section / chart titles).
    parts.append(
        f'text[class*="taskText"] {{ font-weight: {GANTT_TASK_TITLE_FONT_WEIGHT} !important; }}'
    )
    return " ".join(parts)


def gantt_domain_span_days(segments: list[Segment]) -> int:
    """Calendar span of the gantt domain (matches Mermaid time-axis width)."""
    if not segments:
        return 1
    dom_min = min(s.start for s in segments)
    dom_max = max(s.start + timedelta(days=s.duration_days) for s in segments)
    return max(1, (dom_max - dom_min).days)


def tick_label_center_shift_px(
    diagram_width_px: int,
    segments: list[Segment],
    *,
    lr_pad: int = GANTT_AXIS_LR_PADDING,
) -> float:
    """Half of one day’s width in px (mermaid gantt timeScale range / domain span).

    Matches ganttRenderer.js: scale range is ``[0, w - leftPadding - rightPadding]``.
    """
    if not segments:
        return 0.0
    span_days = gantt_domain_span_days(segments)
    inner = max(1, diagram_width_px - 2 * lr_pad)
    return (inner / span_days) / 2.0


def max_chars_for_gantt_bar(
    duration_days: int,
    span_days: int,
    diagram_width_px: int,
    *,
    lr_pad: int = GANTT_AXIS_LR_PADDING,
    px_per_char: float = GANTT_LABEL_PX_PER_CHAR,
    margin: int = GANTT_LABEL_CHAR_MARGIN,
) -> int:
    """Approximate max characters that fit inside a bar (see Mermaid outside-text rule)."""
    inner = max(1, diagram_width_px - 2 * lr_pad)
    span_days = max(1, span_days)
    bar_px = (max(1, duration_days) / span_days) * inner
    return max(4, int(bar_px / px_per_char) - margin)


def build_mermaid_yaml_config_lines(
    rules: list[TopicRule],
    *,
    tick_label_shift_px: float | None = None,
) -> list[str]:
    """YAML frontmatter for theme, topic CSS, and gantt options.

    We avoid %%init%% here: themeCSS contains curly braces which break the
    directive's brace matching. YAML frontmatter parses reliably (see mermaid-js#6260).

    ``displayMode: compact`` packs each Mermaid ``section`` (developer lane) into as few
    horizontal rows as overlap allows; default mode uses one row per task.
    """
    css = build_theme_css(rules, tick_label_shift_px=tick_label_shift_px).replace("'", "''")
    pad = GANTT_AXIS_LR_PADDING
    return [
        "---",
        "config:",
        "  theme: base",
        f"  themeCSS: '{css}'",
        "  gantt:",
        "    topAxis: true",
        "    displayMode: compact",
        f"    leftPadding: {pad}",
        f"    rightPadding: {pad}",
        f"    fontSize: {GANTT_FONT_SIZE}",
        f"    barHeight: {GANTT_BAR_HEIGHT}",
        "---",
    ]


def output_paths(output_dir: Path) -> tuple[Path, Path]:
    """Return (mmd_path, png_path) for a given output directory."""
    return (
        output_dir / OUTPUT["mmd_name"],
        output_dir / OUTPUT["png_name"],
    )


def latest_mmd(output_root: Path) -> Path | None:
    """Find the most recent .mmd file across all timestamped output folders."""
    matches = sorted(
        output_root.glob(f"{OUTPUT['folder_prefix']}-*/{OUTPUT['mmd_name']}"),
        key=lambda p: p.parent.name,
    )
    return matches[-1] if matches else None


def _png_command(mmd_path: Path, png_path: Path) -> list[str]:
    return OUTPUT["mermaid_command"] + [
        "-i", str(mmd_path),
        "-o", str(png_path),
        "-e", "png",
        "-b", OUTPUT["png_background"],
        "-w", str(OUTPUT["png_width"]),
        "-s", str(OUTPUT["png_scale"]),
    ]


def _legend_font(size: int):
    """Best-effort TrueType for the legend; falls back to PIL bitmap font."""
    try:
        from PIL import ImageFont
    except ImportError as e:
        raise ImportError(
            "PNG topic legend requires Pillow. Install with: pip install pillow"
        ) from e

    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def append_topic_legend_to_png(png_path: Path, rules: list[TopicRule], *, scale: int = 1) -> None:
    """Extend the chart PNG downward with a color swatch + label row for each topic rule.

    Internal topics (prefixed with ``_``) are excluded from the legend.
    """
    try:
        from PIL import Image, ImageDraw
        from PIL.ImageColor import getrgb
    except ImportError as e:
        raise ImportError(
            "PNG topic legend requires Pillow. Install with: pip install pillow"
        ) from e

    pad = LEGEND["padding"] * scale
    sw = LEGEND["swatch_size"] * scale
    gap_t = LEGEND["swatch_text_gap"] * scale
    item_gap = LEGEND["item_gap"] * scale
    row_gap = LEGEND["row_gap"] * scale
    title = LEGEND["title"]
    fill_txt = LEGEND["text_color"]
    outline = LEGEND["swatch_outline"]

    font = _legend_font(LEGEND["font_size"] * scale)
    title_font = _legend_font(LEGEND["title_font_size"] * scale)

    chart = Image.open(png_path).convert("RGB")
    w, h0 = chart.size
    inner_w = w - 2 * pad

    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    def item_width(label: str) -> int:
        bbox = probe.textbbox((0, 0), label, font=font)
        return sw + gap_t + (bbox[2] - bbox[0])

    def text_height(label: str) -> int:
        bbox = probe.textbbox((0, 0), label, font=font)
        return bbox[3] - bbox[1]

    rows: list[list[TopicRule]] = []
    row: list[TopicRule] = []
    cw = 0
    for rule in rules:
        iw = item_width(rule.label)
        g = item_gap if row else 0
        if row and cw + g + iw > inner_w:
            rows.append(row)
            row = [rule]
            cw = iw
        else:
            cw += g + iw
            row.append(rule)
    if row:
        rows.append(row)

    tb_title = probe.textbbox((0, 0), title, font=title_font)
    title_h = tb_title[3] - tb_title[1]

    sample_h = text_height("Ay")
    row_line_h = max(sw, sample_h)

    body_h = len(rows) * row_line_h
    if rows:
        body_h += max(0, len(rows) - 1) * row_gap

    legend_h = pad + title_h + row_gap + body_h + pad
    out = Image.new("RGB", (w, h0 + legend_h), OUTPUT["png_background"])
    out.paste(chart, (0, 0))
    draw = ImageDraw.Draw(out)

    y = h0 + pad
    draw.text((pad, y), title, fill=fill_txt, font=title_font)
    y = h0 + pad + title_h + row_gap

    for r_i, row_rules in enumerate(rows):
        x = pad
        for rule in row_rules:
            rgb = getrgb(rule.color)
            draw.rectangle(
                [x, y, x + sw - 1, y + sw - 1],
                fill=rgb,
                outline=getrgb(outline),
                width=1,
            )
            lb = probe.textbbox((0, 0), rule.label, font=font)
            lh = lb[3] - lb[1]
            ty = y + max(0, (sw - lh) // 2)
            draw.text((x + sw + gap_t, ty), rule.label, fill=fill_txt, font=font)
            x += item_width(rule.label) + item_gap
        y += row_line_h
        if r_i < len(rows) - 1:
            y += row_gap

    out.save(png_path, format="PNG")


def render(
    segments: list[Segment],
    rules: list[TopicRule],
    config: CapacityConfig,
    output_dir: Path,
    window_start: date,
    window_end: date,
    jira_stats: dict[str, int],
    merge_stats: dict[str, int],
    local_read_ms: int,
    merge_ms: int,
) -> dict[str, Any]:
    """Render segments to Mermaid + PNG.

    Returns a dict of all pipeline metrics suitable for JSON stdout.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    mmd_path, png_path = output_paths(output_dir)

    # ── Build Mermaid source ──────────────────────────────────────────────────
    sections = MAIN_ASSIGNEES + [ON_HOLD_GANTT_SECTION]
    by_section: dict[str, list[Segment]] = {s: [] for s in sections}
    # Schedule order (order_index) keeps split ticket/capacity chunks consecutive in the section,
    # not interleaved with other work by calendar start date.
    for seg in sorted(segments, key=lambda s: (s.section, s.order_index, s.start, s.task_id)):
        by_section[seg.section].append(seg)

    shift = tick_label_center_shift_px(OUTPUT["png_width"], segments)
    span_days = gantt_domain_span_days(segments)
    lines = [
        *build_mermaid_yaml_config_lines(rules, tick_label_shift_px=shift if shift > 0 else None),
        *mermaid_exclude_comments(config),
        "gantt",
        f"  title {OUTPUT['title']}",
        "  dateFormat YYYY-MM-DD",
        "  axisFormat %A %m/%d",
        "  tickInterval 1day",
        f"  excludes {mermaid_excludes(config)}",
    ]
    wd = mermaid_weekend_directive(config)
    if wd:
        lines.append(f"  weekend {wd}")
    for section in sections:
        lines.append(f"  section {section}")
        for seg in by_section[section]:
            max_c = max_chars_for_gantt_bar(
                seg.duration_days,
                span_days,
                OUTPUT["png_width"],
            )
            label = truncate_gantt_label_with_part(seg.label, max_c)
            lines.append(f"    {label} :{seg.task_id}, {seg.start.isoformat()}, {seg.duration_days}d")

    mermaid = "\n".join(lines) + "\n"
    mmd_path.write_text(mermaid)

    # ── Render PNG (retry once on failure) ───────────────────────────────────
    render_started = time.time()
    render_retries = 0
    cmd = _png_command(mmd_path, png_path)
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        render_retries = 1
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    append_topic_legend_to_png(png_path, rules, scale=OUTPUT["png_scale"])
    render_ms = int((time.time() - render_started) * 1000)
    total_ms = local_read_ms + jira_stats["jira_fetch_ms"] + merge_ms + render_ms

    return {
        **merge_stats,
        **jira_stats,
        "render_retries": render_retries,
        "local_read_ms": local_read_ms,
        "merge_ms": merge_ms,
        "render_ms": render_ms,
        "total_ms": total_ms,
        "output_dir": output_dir.name,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "non_working_days_in_window": non_working_days_in_window(
            config, window_start, window_end
        ),
        "artifacts": [mmd_path.name, png_path.name],
    }
