"""Mermaid gantt generation, PNG rendering, HTML export, and metadata output."""

from __future__ import annotations

import html
import re
import subprocess
import tempfile
import time
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .calendar import (
    mermaid_exclude_comments_for_strip,
    mermaid_excludes_for_strip,
    non_working_days_in_window,
)
from .config import (
    DEFAULT_TYPE_COLOR,
    GANTT_AXIS_LR_PADDING,
    GANTT_BAR_GAP,
    GANTT_BAR_HEIGHT,
    GANTT_BAR_STROKE,
    GANTT_BAR_STROKE_WIDTH,
    GANTT_COMPACT_MODE,
    GANTT_FONT_SIZE,
    GANTT_TASK_TITLE_FONT_WEIGHT,
    GANTT_LABEL_CHAR_MARGIN,
    GANTT_LABEL_PX_PER_CHAR,
    LEGEND,
    GANTT_LANE_ASSIGNEES,
    OUTPUT,
    UNASSIGNED_SENTINEL,
)
from .models import CapacityConfig, Segment, TypeRule, truncate_gantt_label_with_part


def types_referenced_by_segments(segments: list[Segment]) -> set[str]:
    """Type slugs used in gantt bar task ids (for CSS selectors and legend)."""
    out: set[str] = set()
    for seg in segments:
        tid = seg.task_id
        if tid.startswith("capacity_"):
            out.add("capacity")
        else:
            mark = "_ATB-"
            if mark in tid:
                out.add(tid.split(mark, 1)[0])
    return out


def resolve_render_type_rules(
    file_rules: list[TypeRule],
    config_rules: list[TypeRule],
    segments: list[Segment],
) -> list[TypeRule]:
    """Build ordered type rules for Mermaid CSS + legend.

    Colours and legend order follow ``file_rules`` when present; any type that
    appears in ``segments`` but is missing there is filled from ``config_rules``.
    """
    types_used = types_referenced_by_segments(segments)
    if not file_rules:
        file_rules = list(config_rules)
    seen: set[str] = set()
    out: list[TypeRule] = []
    for r in file_rules:
        if r.type_id in types_used:
            out.append(r)
            seen.add(r.type_id)
    for r in config_rules:
        if r.type_id in types_used and r.type_id not in seen:
            out.append(r)
            seen.add(r.type_id)
    for t in sorted(types_used - seen):
        out.append(TypeRule(type_id=t, label=t.replace("_", " "), color=DEFAULT_TYPE_COLOR))
    return out


def build_theme_css(
    rules: list[TypeRule],
    *,
    tick_label_shift_px: float | None = None,
) -> str:
    """Generate inline CSS for Jira Type colour coding in the Mermaid gantt."""
    sw = GANTT_BAR_STROKE_WIDTH
    sc = GANTT_BAR_STROKE
    parts = [
        (
            f'rect[id*="{rule.type_id}_"] {{ fill: {rule.color} !important; '
            f"stroke: {sc} !important; stroke-width: {sw}px !important; }}"
        )
        for rule in rules
    ]
    # Invisible full-strip bar so Mermaid keeps a fixed Sun–Thu (5-day) axis per weekly strip.
    parts.append(
        f'rect[id*="{AXIS_PAD_TASK_PREFIX}"] {{ opacity: 0 !important; stroke: none !important; }}'
        f' g[id*="{AXIS_PAD_TASK_PREFIX}"] text {{ opacity: 0 !important; }}'
    )
    # Ticks sit on day boundaries (midnight); shift by half a day-width to center on the column.
    tick_styles = ["fill: #334155 !important"]
    if tick_label_shift_px is not None and tick_label_shift_px > 0:
        tick_styles.append(f"transform: translateX({tick_label_shift_px:.3f}px)")
    parts.append("g.grid g.tick text { " + "; ".join(tick_styles) + " }")
    # Bold task titles; dark fill reads on bright fills and on neutral ``other`` bars.
    # (Both lines must be f-strings: a plain ``"...}}"`` would emit ``}}`` and break themeCSS.)
    parts.append(
        f'text[class*="taskText"] {{ font-weight: {GANTT_TASK_TITLE_FONT_WEIGHT} !important; '
        f'fill: #0f172a !important; }}'
    )
    parts.append('g[class*="title"] text, text[class*="titleText"] { fill: #0f172a !important; }')
    return " ".join(parts)


def gantt_domain_span_days(segments: list[Segment]) -> int:
    """Calendar span of the gantt domain (matches Mermaid time-axis width)."""
    if not segments:
        return 1
    dom_min = min(s.start for s in segments)
    dom_max = max(s.start + timedelta(days=s.duration_days) for s in segments)
    return max(1, (dom_max - dom_min).days)


# Mermaid gantt scales the time axis to the min/max of all tasks; this pins a fixed width.
# Section / task ids must not be empty or leading-underscore (breaks the gantt parser).
AXIS_PAD_SECTION = "week_axis"
AXIS_PAD_TASK_PREFIX = "gantt_axis_pad_"


def _gantt_task_line(
    seg: Segment,
    *,
    max_c: int,
    strip_exclusive_end: date | None = None,
) -> str:
    """Emit one gantt task row.

    The axis pad uses **start + end date** (not ``Nd``) so the chart domain stays
    exactly ``[strip_start, strip_exclusive_end)`` even when ``excludes`` lists
    holidays inside that range. Per Mermaid docs, duration-based tasks extend past
    excluded days to preserve nominal length, which would stretch the axis and
    shrink day columns vs strips without excludes.
    """
    label = truncate_gantt_label_with_part(seg.label, max_c)
    if (
        strip_exclusive_end is not None
        and seg.task_id.startswith(AXIS_PAD_TASK_PREFIX)
    ):
        last_inclusive = strip_exclusive_end - timedelta(days=1)
        return f"    {label} :{seg.task_id}, {seg.start.isoformat()}, {last_inclusive.isoformat()}"
    return f"    {label} :{seg.task_id}, {seg.start.isoformat()}, {seg.duration_days}d"


def iter_sunday_thursday_strips(
    window_start: date,
    window_end_inclusive: date,
) -> list[tuple[date, date]]:
    """Sunday-aligned working-week strips overlapping [window_start, window_end_inclusive].

    Each item is ``(strip_start_sunday, strip_exclusive_end)`` where the visible axis
    is ``[strip_start_sunday, strip_exclusive_end)`` — **five** calendar days (Sunday
    through Thursday). Friday and Saturday are not part of the Gantt domain.
    """
    if window_end_inclusive < window_start:
        return []
    # Sunday of the week containing window_start (Mon=0 … Sun=6).
    first_sunday = window_start - timedelta(days=(window_start.weekday() + 1) % 7)
    out: list[tuple[date, date]] = []
    cur = first_sunday
    while cur <= window_end_inclusive:
        strip_exclusive_end = cur + timedelta(days=5)
        if strip_exclusive_end > window_start and cur <= window_end_inclusive:
            out.append((cur, strip_exclusive_end))
        cur += timedelta(days=7)
    return out


def clip_segment_to_window(
    seg: Segment,
    win_start: date,
    win_exclusive_end: date,
) -> Segment | None:
    """Intersect ``seg`` with ``[win_start, win_exclusive_end)``; drop if empty."""
    seg_end = seg.start + timedelta(days=seg.duration_days)
    overlap_start = max(seg.start, win_start)
    overlap_end = min(seg_end, win_exclusive_end)
    if overlap_start >= overlap_end:
        return None
    new_dur = (overlap_end - overlap_start).days
    if new_dur < 1:
        return None
    if overlap_start == seg.start and new_dur == seg.duration_days:
        return seg
    return replace(seg, start=overlap_start, duration_days=new_dur)


def clip_segments_to_week_window(
    segments: list[Segment],
    strip_start: date,
    strip_exclusive_end: date,
) -> list[Segment]:
    """Clip every segment to the strip window; preserves section ordering via stable sort."""
    out: list[Segment] = []
    for seg in segments:
        clipped = clip_segment_to_window(seg, strip_start, strip_exclusive_end)
        if clipped is not None:
            out.append(clipped)
    return sorted(out, key=lambda s: (s.section, s.order_index, s.start, s.task_id))


def week_strip_title(strip_start_sunday: date, strip_exclusive_end: date) -> str:
    """Human-readable strip range for the gantt title (Sun … Thu)."""
    last = strip_exclusive_end - timedelta(days=1)
    return f"{OUTPUT['title']} — {strip_start_sunday.strftime('%b %d')}–{last.strftime('%b %d, %Y')}"


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
    rules: list[TypeRule],
    *,
    tick_label_shift_px: float | None = None,
) -> list[str]:
    """YAML frontmatter for theme, Type CSS, and gantt options.

    We avoid %%init%% here: themeCSS contains curly braces which break the
    directive's brace matching. YAML frontmatter parses reliably (see mermaid-js#6260).

    Optional ``GANTT_COMPACT_MODE`` enables ``displayMode: compact`` (shared rows); default
    is one row per task for readability.
    """
    css = build_theme_css(rules, tick_label_shift_px=tick_label_shift_px).replace("'", "''")
    pad = GANTT_AXIS_LR_PADDING
    lines: list[str] = [
        "---",
        "config:",
        "  theme: base",
        f"  themeCSS: '{css}'",
        "  gantt:",
        "    topAxis: true",
    ]
    if GANTT_COMPACT_MODE:
        lines.append("    displayMode: compact")
    lines.extend(
        [
            f"    leftPadding: {pad}",
            f"    rightPadding: {pad}",
            f"    fontSize: {GANTT_FONT_SIZE}",
            f"    barHeight: {GANTT_BAR_HEIGHT}",
            f"    barGap: {GANTT_BAR_GAP}",
            "---",
        ]
    )
    return lines


def output_paths(output_dir: Path) -> tuple[Path, Path, Path]:
    """Return (mmd_path, png_path, html_path) for a given output directory."""
    return (
        output_dir / OUTPUT["mmd_name"],
        output_dir / OUTPUT["png_name"],
        output_dir / OUTPUT["html_name"],
    )


def _html_bar_geometry(
    seg: Segment,
    strip_start: date,
    strip_exclusive_end: date,
) -> tuple[float, float] | None:
    """Return ``(left_pct, width_pct)`` of the bar within the Sun–Thu strip, or None if empty."""
    span_days = (strip_exclusive_end - strip_start).days
    if span_days <= 0:
        return None
    seg_end = seg.start + timedelta(days=seg.duration_days)
    clip_lo = max(seg.start, strip_start)
    clip_hi = min(seg_end, strip_exclusive_end)
    if clip_lo >= clip_hi:
        return None
    left_days = (clip_lo - strip_start).days
    width_days = (clip_hi - clip_lo).days
    return 100.0 * left_days / span_days, 100.0 * width_days / span_days


def build_team_timeline_html(
    segments: list[Segment],
    rules: list[TypeRule],
    window_start: date,
    window_end: date,
) -> str:
    """Static HTML with the same weekly Sun–Thu strips as the PNG; bars show details on hover (CSS tooltip)."""
    weeks = iter_sunday_thursday_strips(window_start, window_end)
    if not weeks:
        weeks = [(window_start, window_start + timedelta(days=5))]

    color_by_type = {r.type_id: r.color for r in rules}
    default_color = DEFAULT_TYPE_COLOR
    assignees = [a for a in GANTT_LANE_ASSIGNEES if a != UNASSIGNED_SENTINEL]

    strip_sections: list[str] = []
    for strip_start, strip_exclusive_end in weeks:
        clipped = clip_segments_to_week_window(segments, strip_start, strip_exclusive_end)
        visible = [
            s
            for s in clipped
            if not s.task_id.startswith(AXIS_PAD_TASK_PREFIX) and s.section != UNASSIGNED_SENTINEL
        ]
        strip_title = html.escape(week_strip_title(strip_start, strip_exclusive_end))

        day_cells: list[str] = []
        for i in range((strip_exclusive_end - strip_start).days):
            d = strip_start + timedelta(days=i)
            day_cells.append(
                f'<div class="day-hd">{html.escape(d.strftime("%a %b"))} {d.day}</div>'
            )
        day_row = f'<div class="day-headers">{"".join(day_cells)}</div>'

        lane_rows: list[str] = []
        for person in assignees:
            lane_segs = sorted(
                [s for s in visible if s.section == person],
                key=lambda s: (s.order_index, s.start, s.task_id),
            )
            bar_html: list[str] = []
            for seg in lane_segs:
                geom = _html_bar_geometry(seg, strip_start, strip_exclusive_end)
                if geom is None:
                    continue
                left_pct, width_pct = geom
                fill = color_by_type.get(seg.type_id, default_color)
                tip = html.escape(seg.tooltip) if seg.tooltip else ""
                lbl = html.escape(seg.label)
                # Native `title` is flaky in IDE embedded previews; CSS hover tip works everywhere.
                tip_block = (
                    f'<div class="bar-tip" role="tooltip">{tip}</div>' if tip else ""
                )
                bar_html.append(
                    f'<div class="bar-wrap" style="left:{left_pct:.4f}%;width:{width_pct:.4f}%;">'
                    f'<div class="bar" style="background:{fill}">{lbl}</div>{tip_block}</div>'
                )
            lane_rows.append(
                f'<div class="lane"><div class="lane-name">{html.escape(person)}</div>'
                f'<div class="lane-track"><div class="lane-bars">{"".join(bar_html)}</div></div></div>'
            )

        strip_sections.append(
            f'<section class="strip"><h2 class="strip-title">{strip_title}</h2>'
            f"{day_row}{''.join(lane_rows)}</section>"
        )

    legend_items = "".join(
        f'<span class="leg-item"><span class="leg-swatch" style="background:{html.escape(r.color)}"></span>'
        f"{html.escape(r.label)}</span>"
        for r in rules
    )
    legend_block = (
        f'<section class="legend"><h3>{html.escape(LEGEND["title"])}</h3><div>{legend_items}</div></section>'
    )
    win = f"{window_start.isoformat()} — {window_end.isoformat()}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(OUTPUT["title"])}</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; padding: 24px;
      background: #f8fafc; color: #0f172a; }}
    h1 {{ font-size: 1.25rem; margin: 0 0 8px 0; }}
    .sub {{ color: #64748b; font-size: 0.9rem; margin-bottom: 24px; }}
    .strip {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 20px; }}
    .strip-title {{ font-size: 1rem; margin: 0 0 12px 0; font-weight: 600; }}
    .day-headers {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px; margin-bottom: 8px;
      font-size: 0.75rem; color: #64748b; text-align: center; }}
    .lane {{ display: flex; align-items: stretch; gap: 12px; margin-bottom: 8px; min-height: 40px; }}
    .lane-name {{ width: 100px; flex-shrink: 0; font-size: 0.85rem; font-weight: 500; padding-top: 8px; }}
    .lane-track {{ flex: 1; min-width: 0; border: 1px solid #cbd5e1; border-radius: 4px;
      background: linear-gradient(to right, #f1f5f9 0%, #f1f5f9 100%); position: relative; }}
    .lane-bars {{ position: relative; height: 36px; }}
    .bar-wrap {{ position: absolute; top: 4px; height: 28px; z-index: 1; }}
    .bar-wrap:hover {{ z-index: 50; }}
    .bar {{ height: 100%; width: 100%; border-radius: 4px; box-sizing: border-box;
      padding: 2px 6px; font-size: 11px; font-weight: 600; line-height: 1.2; overflow: hidden;
      text-overflow: ellipsis; white-space: nowrap; border: 1px solid rgba(15, 23, 42, 0.12);
      color: #0f172a; cursor: help; }}
    .bar-tip {{
      display: none; position: absolute; bottom: calc(100% + 6px); left: 0; min-width: 260px; max-width: min(520px, 90vw);
      padding: 8px 10px; background: #1e293b; color: #f1f5f9; font-size: 12px; font-weight: 400;
      line-height: 1.35; border-radius: 6px; box-shadow: 0 6px 20px rgba(15, 23, 42, 0.25);
      white-space: pre-line; word-break: break-word; pointer-events: none; text-align: left;
    }}
    .bar-wrap:hover .bar-tip {{ display: block; }}
    .legend {{ margin: 0 0 20px 0; padding: 16px; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; }}
    .legend h3 {{ margin: 0 0 12px 0; font-size: 0.95rem; }}
    .leg-item {{ display: inline-flex; align-items: center; gap: 8px; margin-right: 20px; margin-bottom: 8px;
      font-size: 0.85rem; }}
    .leg-swatch {{ width: 14px; height: 14px; border-radius: 3px; border: 1px solid rgba(15,23,42,0.15); }}
  </style>
</head>
<body>
  <h1>{html.escape(OUTPUT["title"])}</h1>
  <p class="sub">Planning window (inclusive): {html.escape(win)} · Hover a bar for labels, parent, title, assignee, estimation, and status.</p>
  {legend_block}
  {"".join(strip_sections)}
</body>
</html>
"""


def latest_mmd(output_root: Path) -> Path | None:
    """Find the most recent .mmd file across all timestamped output folders."""
    matches = sorted(
        output_root.glob(f"{OUTPUT['folder_prefix']}-*/{OUTPUT['mmd_name']}"),
        key=lambda p: p.parent.name,
    )
    return matches[-1] if matches else None


# Combined build output concatenates one ``%% Week strip i/n`` block per Sun–Thu strip.
_STRIP_SPLIT = re.compile(r"\n\n(?=%% Week strip \d+/\d+:)", re.MULTILINE)


def first_mermaid_diagram_for_smoke(mmd_path: Path) -> str:
    """Mermaid source for a single diagram (first stacked strip), or the whole file if not multi-strip.

    Leading ``%%`` lines (e.g. the ``%% Week strip i/n`` banner) are removed so the file starts
    with ``---`` — mermaid-cli requires YAML frontmatter first.
    """
    text = mmd_path.read_text()
    parts = _STRIP_SPLIT.split(text)
    chunk = parts[0] if len(parts) > 1 else text
    lines = chunk.strip().splitlines()
    while lines and lines[0].strip().startswith("%%"):
        lines.pop(0)
    out = "\n".join(lines)
    if not out.endswith("\n"):
        out += "\n"
    return out


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
            "PNG Type legend requires Pillow. Install with: pip install pillow"
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


def append_type_legend_to_png(png_path: Path, rules: list[TypeRule], *, scale: int = 1) -> None:
    """Extend the chart PNG downward with a color swatch + label row for each type rule.

    Internal types (prefixed with ``_``) are excluded from the legend.
    """
    try:
        from PIL import Image, ImageDraw
        from PIL.ImageColor import getrgb
    except ImportError as e:
        raise ImportError(
            "PNG Type legend requires Pillow. Install with: pip install pillow"
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

    rows: list[list[TypeRule]] = []
    row: list[TypeRule] = []
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


# Vertical gap between stacked weekly Gantt PNGs (pixels at 1×; mmdc output is scaled separately).
WEEK_STRIP_GAP_PX = 20


def stitch_pngs_vertical(paths: list[Path], out: Path, *, gap_px: int) -> None:
    """Stack PNGs top-to-bottom on a shared background; centers strips if widths differ."""
    try:
        from PIL import Image
    except ImportError as e:
        raise ImportError(
            "Stacked weekly charts require Pillow. Install with: pip install pillow"
        ) from e

    if not paths:
        raise ValueError("stitch_pngs_vertical requires at least one PNG")
    imgs = [Image.open(p).convert("RGB") for p in paths]
    w = max(im.size[0] for im in imgs)
    total_h = sum(im.size[1] for im in imgs) + gap_px * (len(imgs) - 1)
    bg = OUTPUT["png_background"]
    canvas = Image.new("RGB", (w, total_h), bg)
    y = 0
    for i, im in enumerate(imgs):
        x = max(0, (w - im.size[0]) // 2)
        canvas.paste(im, (x, y))
        y += im.size[1]
        if i < len(imgs) - 1:
            y += gap_px
    canvas.save(out, format="PNG")


def build_week_mermaid(
    segments_in_week: list[Segment],
    rules: list[TypeRule],
    config: CapacityConfig,
    *,
    title: str,
    strip_start_sunday: date,
    strip_exclusive_end: date,
) -> str:
    """One Mermaid document: Sun–Thu strip with a hidden 5-day bar for axis width (no Fri/Sat)."""
    assignee_sections = [a for a in GANTT_LANE_ASSIGNEES if a != UNASSIGNED_SENTINEL]
    sections = [AXIS_PAD_SECTION] + assignee_sections
    visible_segments = [s for s in segments_in_week if s.section != UNASSIGNED_SENTINEL]
    strip_days = (strip_exclusive_end - strip_start_sunday).days
    pad = Segment(
        label="·",
        task_id=f"{AXIS_PAD_TASK_PREFIX}{strip_start_sunday.isoformat()}",
        section=AXIS_PAD_SECTION,
        start=strip_start_sunday,
        duration_days=strip_days,
        order_index=0,
    )
    all_segments = [pad] + visible_segments
    by_section: dict[str, list[Segment]] = {s: [] for s in sections}
    for seg in sorted(all_segments, key=lambda s: (s.section, s.order_index, s.start, s.task_id)):
        by_section[seg.section].append(seg)

    shift = tick_label_center_shift_px(OUTPUT["png_width"], all_segments)
    span_days = gantt_domain_span_days(all_segments)
    excl = mermaid_excludes_for_strip(config, strip_start_sunday, strip_exclusive_end)
    lines = [
        *build_mermaid_yaml_config_lines(rules, tick_label_shift_px=shift if shift > 0 else None),
        *mermaid_exclude_comments_for_strip(config, strip_start_sunday, strip_exclusive_end),
        "gantt",
        f"  title {title}",
        "  dateFormat YYYY-MM-DD",
        "  axisFormat %A %m/%d",
        "  tickInterval 1day",
    ]
    if excl:
        lines.append(f"  excludes {excl}")
    for section in sections:
        lines.append(f"  section {section}")
        for seg in by_section[section]:
            max_c = max_chars_for_gantt_bar(
                seg.duration_days,
                span_days,
                OUTPUT["png_width"],
            )
            lines.append(
                _gantt_task_line(
                    seg,
                    max_c=max_c,
                    strip_exclusive_end=strip_exclusive_end,
                )
            )

    return "\n".join(lines) + "\n"


def _run_mmdc_to_png(mmd_path: Path, png_path: Path) -> int:
    """Invoke mermaid-cli; retry once on failure. Returns number of retries (0 or 1)."""
    cmd = _png_command(mmd_path, png_path)
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return 0
    except subprocess.CalledProcessError:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return 1


def render(
    segments: list[Segment],
    rules: list[TypeRule],
    config: CapacityConfig,
    output_dir: Path,
    window_start: date,
    window_end: date,
    jira_stats: dict[str, int],
    merge_stats: dict[str, int],
    local_read_ms: int,
    merge_ms: int,
) -> dict[str, Any]:
    """Render segments to Mermaid + PNG + HTML.

    The chart is split into Sunday–Thursday (working-week) Gantt strips stacked
    vertically; Friday and Saturday are omitted from the axis (not greyed).
    The HTML file mirrors the same strips; task bars expose Jira metadata on hover.

    Returns a dict of all pipeline metrics suitable for JSON stdout.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    mmd_path, png_path, html_path = output_paths(output_dir)

    weeks = iter_sunday_thursday_strips(window_start, window_end)
    if not weeks:
        weeks = [(window_start, window_start + timedelta(days=5))]

    render_started = time.time()
    render_retries = 0
    mmd_blocks: list[str] = []
    week_png_paths: list[Path] = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for i, (strip_start, strip_exclusive_end) in enumerate(weeks):
            clipped = clip_segments_to_week_window(segments, strip_start, strip_exclusive_end)
            title = week_strip_title(strip_start, strip_exclusive_end)
            block = build_week_mermaid(
                clipped,
                rules,
                config,
                title=title,
                strip_start_sunday=strip_start,
                strip_exclusive_end=strip_exclusive_end,
            )
            mmd_blocks.append(f"%% Week strip {i + 1}/{len(weeks)}: {strip_start.isoformat()} (Sun–Thu) …\n{block}")
            w_mmd = tmp_dir / f"week-{i}.mmd"
            w_png = tmp_dir / f"week-{i}.png"
            w_mmd.write_text(block)
            render_retries += _run_mmdc_to_png(w_mmd, w_png)
            week_png_paths.append(w_png)

        mmd_path.write_text("\n\n".join(mmd_blocks) + "\n")
        stitch_pngs_vertical(week_png_paths, png_path, gap_px=WEEK_STRIP_GAP_PX)

    append_type_legend_to_png(png_path, rules, scale=OUTPUT["png_scale"])
    html_path.write_text(
        build_team_timeline_html(segments, rules, window_start, window_end),
        encoding="utf-8",
    )
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
        "gantt_weekly_strips": len(weeks),
        "non_working_days_in_window": non_working_days_in_window(
            config, window_start, window_end
        ),
        "artifacts": [mmd_path.name, png_path.name, html_path.name],
        # Clickable in chat/IDE: [Open timeline](<html_file_uri>)
        "html_path": str(html_path.resolve()),
        "html_file_uri": html_path.resolve().as_uri(),
    }
