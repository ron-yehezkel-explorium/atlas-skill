"""Static configuration for the team timeline pipeline.

Edit this file to change capacity, holidays, on-call rotation, Jira field ids, or output settings.
"""

from __future__ import annotations

from .models import CapacityConfig, CapacityEvent, TypeRule, type_id_from_jira_label

TIMEZONE = "Asia/Jerusalem"
DEFAULT_VIEW_DAYS = 30

OUTPUT = {
    "root_dir_name": "output",
    "folder_prefix": "Team-Timeline",
    "title": "Team Timeline",
    "mmd_name": "team-timeline.mmd",
    "png_name": "team-timeline.png",
    "html_name": "team-timeline.html",
    "mermaid_command": ["npx", "-y", "@mermaid-js/mermaid-cli"],
    # Diagram width (px); lower = narrower day columns on Sun–Thu strips. Tuned vs default 5200.
    "png_width": 1400,
    "png_scale": 2,
    "png_background": "white",
}

# Strip appended below the Mermaid PNG: swatches + Type labels (see ``append_type_legend_to_png``).
LEGEND = {
    "title": "Type colors",
    "padding": 24,
    "title_font_size": 16,
    "font_size": 14,
    "swatch_size": 16,
    "swatch_text_gap": 8,
    "item_gap": 28,
    "row_gap": 10,
    "text_color": "#222222",
    "swatch_outline": "#9aa0a6",
}

# Mermaid gantt left/right padding; must match YAML `gantt.leftPadding` / `rightPadding` in render.
GANTT_AXIS_LR_PADDING = 38
# Mermaid draws labels outside bars when text is wider than the bar (ganttRenderer). We truncate
# titles to fit the bar width; tune px/char if truncation is too aggressive or still overflows.
GANTT_FONT_SIZE = 11
# CSS font-weight for task row labels (Mermaid classes taskText / taskTextOutside*).
GANTT_TASK_TITLE_FONT_WEIGHT = 700
GANTT_BAR_HEIGHT = 28
# Mermaid default is 4; vertical space between consecutive task rows.
GANTT_BAR_GAP = 12
# White outline so adjacent bars (incl. same color on one row in compact mode) stay distinct.
GANTT_BAR_STROKE = "#ffffff"
GANTT_BAR_STROKE_WIDTH = 6
# True = ``displayMode: compact`` (tasks share rows when possible). White stroke still separates segments.
GANTT_COMPACT_MODE = True
GANTT_LABEL_PX_PER_CHAR = 5.5
GANTT_LABEL_CHAR_MARGIN = 2

JIRA = {
    "backend": "acli",
    "site": "exploriumai.atlassian.net",
    "project": "ATB",
    "board_id": "154",
    "tracked_statuses": ["In Progress", "To Do"],
    "search_page_size": 200,
    # ``type_field_id`` is appended at fetch time (see ``jira_fetch._jira_search_fields``).
    "search_fields": "key,summary,labels,assignee,status,issuetype",
    # Required single-select “Type” on ATB work items (option ``value`` strings drive colours + legend).
    "type_field_id": "customfield_10264",
    # Used with REST createmeta when ``use_createmeta_for_type_order`` is True.
    "createmeta_issue_type_id": "10157",
    # If True, legend colour order follows Jira’s full Type option list (createmeta). If False (default),
    # only Type values present on fetched issues are used — avoids legacy option names cluttering the legend.
    "use_createmeta_for_type_order": False,
    "status_jql": {
        "In Progress": 'project = ATB AND status = "In Progress" ORDER BY Rank ASC',
        "To Do": 'project = ATB AND status = "To Do" ORDER BY Rank ASC',
    },
}

ROSTER = {
    "main_assignees": ["ron", "yaara", "rani", "itai", "danielle", "unassigned"],
    "aliases": {
        "ron": {"ron", "ron yehezkel", "ron.yehezkel", "ron.yehezkel@explorium.ai", "@ron.yehezkel"},
        "yaara": {"yaara", "yaara yona", "yaara.yona", "yaara.yona@explorium.ai", "@yaara.yona"},
        "rani": {"rani", "rani khoury", "rani.khoury", "rani.khoury@explorium.ai", "@rani.khoury"},
        "itai": {"itai", "itai dagan", "itai.dagan", "itai.dagan@explorium.ai", "@itai.dagan"},
        "danielle": {"danielle", "danielle gan", "danielle.gan", "danielle.gan@explorium.ai", "@danielle.gan"},
    },
}

# Jira Type colours by slug (``type_id_from_jira_label``). Keys must match how Jira option names slugify.
# Very light, high-luminance pastels for maximum on-screen pop vs dark bar text (#0f172a).
TYPE_COLOR_BY_SLUG: dict[str, str] = {
    "contacts": "#ffc8e4",       # cotton-candy pink
    "firmo": "#edc8ff",          # bright lavender
    "firmographics": "#edc8ff",
    "delivery": "#a8ffd0",     # neon mint
    "deliveries": "#a8ffd0",
    "other": "#ffffff",
    "tech": "#fff9a8",           # light lemon
    "tech_debt": "#fff9a8",
    "data": "#b8ecff",           # icy sky blue
}
DEFAULT_TYPE_COLOR = "#e8f7ff"  # airy blue for unmapped types

# Synthetic capacity / on-call / PTO rows (not a Jira Type).
CAPACITY_TYPE_RULE = TypeRule(type_id="capacity", label="Capacity", color="#eef2f9")

# Non-working calendar (grey gantt columns + scheduling skips):
# - working_days: which weekdays count toward ticket effort (see schedule/allocate_segments).
# - weekend_days: drawn as non-working in Mermaid (excludes) and listed in build JSON
#   as non_working_days_in_window for each date in the view.
# - global_non_working_days: team-wide holidays (add ISO start_date, duration_days, label).
# - per_person_capacity_events: PTO / etc. — bars in that assignee’s lane only; they do not
#   grey out the whole column for everyone.
CAPACITY = {
    "working_days": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"],
    "weekend_days": ["Friday", "Saturday"],
    "global_non_working_days": [],
    "on_call": {
        "changeover": "Tuesday 12:00",
        "representation_label": "On-call",
        "representation_duration_days": 1,
        "current_oncall": "ron",
        "rotation_order": ["ron", "yaara", "rani", "itai", "danielle"],
    },
    "per_person_capacity_events": {
        "ron": [{"start_date": "2026-04-08", "duration_days": 1, "label": "Team holiday"}],
        "yaara": [{"start_date": "2026-04-08", "duration_days": 1, "label": "Team holiday"}],
        "rani": [],
        "itai": [{"start_date": "2026-04-08", "duration_days": 1, "label": "Team holiday"}],
        "danielle": [{"start_date": "2026-04-08", "duration_days": 1, "label": "Team holiday"}],
        "unassigned": [{"start_date": "2026-04-08", "duration_days": 1, "label": "Team holiday"}],
    },
}

# ── Derived constants (computed once at import) ───────────────────────────────

STATUSES: list[str] = JIRA["tracked_statuses"]
MAIN_ASSIGNEES: list[str] = ROSTER["main_assignees"]

# Omit these assignee rows from the chart only (markdown + Jira still use full roster).
GANTT_EXCLUDE_LANES: frozenset[str] = frozenset({"ron"})
GANTT_LANE_ASSIGNEES: list[str] = [a for a in MAIN_ASSIGNEES if a not in GANTT_EXCLUDE_LANES]

# Sentinel strings — all team-specific literals live here, nowhere else.
UNASSIGNED_SENTINEL: str = "unassigned"           # fallback assignee for unknown/null Jira users
UNRESOLVABLE_NAMES: frozenset[str] = frozenset({"former user", "unassigned"})  # treated as unassigned
DEFAULT_JIRA_TYPE: str = "Other"                  # fallback if Type is missing in Jira or locally


# ── Factory functions ─────────────────────────────────────────────────────────

def color_for_jira_type_label(label: str) -> str:
    """Resolved fill for a Jira Type option name."""
    lid = type_id_from_jira_label(label)
    return TYPE_COLOR_BY_SLUG.get(lid, DEFAULT_TYPE_COLOR)


def type_rules_for_jira_labels(ordered_labels: list[str]) -> list[TypeRule]:
    """Build TypeRule rows for each Jira Type option label (exact Jira ``value`` strings)."""
    rules: list[TypeRule] = []
    for label in ordered_labels:
        lid = type_id_from_jira_label(label)
        rules.append(
            TypeRule(
                type_id=lid,
                label=label.strip(),
                color=color_for_jira_type_label(label),
            )
        )
    return rules


def default_type_rules_with_capacity(ordered_jira_labels: list[str]) -> list[TypeRule]:
    """Palette rules for all Jira types plus the synthetic capacity lane."""
    return [*type_rules_for_jira_labels(ordered_jira_labels), CAPACITY_TYPE_RULE]


def capacity_config() -> CapacityConfig:
    """Instantiate CapacityConfig from the CAPACITY config."""
    return CapacityConfig(
        timezone=TIMEZONE,
        working_days=CAPACITY["working_days"],
        weekend_days=CAPACITY["weekend_days"],
        changeover=CAPACITY["on_call"]["changeover"],
        representation_label=CAPACITY["on_call"]["representation_label"],
        representation_duration_days=CAPACITY["on_call"]["representation_duration_days"],
        current_oncall=CAPACITY["on_call"]["current_oncall"],
        rotation_order=CAPACITY["on_call"]["rotation_order"],
        global_non_working_days=[CapacityEvent(**item) for item in CAPACITY["global_non_working_days"]],
        per_person_capacity_events={
            person: [CapacityEvent(**event) for event in events]
            for person, events in CAPACITY["per_person_capacity_events"].items()
        },
    )
