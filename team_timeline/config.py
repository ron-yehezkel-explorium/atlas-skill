"""Static configuration for the team timeline pipeline.

Edit this file to change topics, capacity, holidays, on-call rotation, or Jira defaults.
"""

from __future__ import annotations

from .models import CapacityConfig, CapacityEvent, TopicRule

TIMEZONE = "Asia/Jerusalem"
DEFAULT_VIEW_DAYS = 30

OUTPUT = {
    "root_dir_name": "output",
    "folder_prefix": "Team-Timeline",
    "title": "Team Timeline",
    "mmd_name": "team-timeline.mmd",
    "png_name": "team-timeline.png",
    "mermaid_command": ["npx", "-y", "@mermaid-js/mermaid-cli"],
    # Diagram width (px); lower = narrower day columns on Sun–Thu strips. Tuned vs default 5200.
    "png_width": 1400,
    "png_scale": 2,
    "png_background": "white",
}

# Strip appended below the Mermaid PNG: swatches + topic labels (see ``append_topic_legend_to_png``).
LEGEND = {
    "title": "Topic colors",
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
GANTT_BAR_HEIGHT = 24
GANTT_LABEL_PX_PER_CHAR = 5.5
GANTT_LABEL_CHAR_MARGIN = 2

JIRA = {
    "backend": "acli",
    "site": "exploriumai.atlassian.net",
    "project": "ATB",
    "board_id": "154",
    "tracked_statuses": ["In Progress", "To Do", "On Hold"],
    "search_page_size": 200,
    "search_fields": "key,summary,labels,assignee,status,issuetype",
    "status_jql": {
        "In Progress": 'project = ATB AND status = "In Progress" ORDER BY Rank ASC',
        "To Do": 'project = ATB AND status = "To Do" ORDER BY Rank ASC',
        "On Hold": 'project = ATB AND status = "On Hold" ORDER BY Rank ASC',
    },
}

ROSTER = {
    "main_assignees": ["ron", "yaara", "rani", "itai", "danielle", "unassigned"],
    "on_hold_assignees": ["shared"],
    "aliases": {
        "ron": {"ron", "ron yehezkel", "ron.yehezkel", "ron.yehezkel@explorium.ai", "@ron.yehezkel"},
        "yaara": {"yaara", "yaara yona", "yaara.yona", "yaara.yona@explorium.ai", "@yaara.yona"},
        "rani": {"rani", "rani khoury", "rani.khoury", "rani.khoury@explorium.ai", "@rani.khoury"},
        "itai": {"itai", "itai dagan", "itai.dagan", "itai.dagan@explorium.ai", "@itai.dagan"},
        "danielle": {"danielle", "danielle gan", "danielle.gan", "danielle.gan@explorium.ai", "@danielle.gan"},
    },
}

# Topic metadata for gantt bar colours and the PNG legend.
# New Jira issues default to ``DEFAULT_TOPIC`` until you set ``topic`` in the tickets file.
TOPICS = [
    {"topic": "contacts", "label": "Contacts", "color": "#2563EB"},
    {"topic": "firmo", "label": "Firmographics", "color": "#9333EA"},
    {"topic": "deliveries", "label": "Deliveries", "color": "#15803D"},
    {"topic": "tech_debt", "label": "Tech debt", "color": "#FF9F1C"},
    {"topic": "other", "label": "Other", "color": "#64748B"},
    {"topic": "capacity", "label": "Capacity", "color": "#8B8FA3"},
    {"topic": "on_hold", "label": "On Hold", "color": "#C44569"},
]

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
    "global_non_working_days": [
        {"start_date": "2026-04-16", "duration_days": 1, "label": "Team day"},
    ],
    "on_call": {
        "changeover": "Tuesday 12:00",
        "representation_label": "On-call",
        "representation_duration_days": 1,
        "current_oncall": "ron",
        "rotation_order": ["ron", "yaara", "rani", "itai", "danielle"],
    },
    "per_person_capacity_events": {
        "ron": [{"start_date": "2026-04-06", "duration_days": 1, "label": "Ron vacation"}],
        "yaara": [], "rani": [], "itai": [], "danielle": [], "unassigned": [],
    },
}

# ── Derived constants (computed once at import) ───────────────────────────────

STATUSES: list[str] = JIRA["tracked_statuses"]
MAIN_ASSIGNEES: list[str] = ROSTER["main_assignees"]
ON_HOLD_ASSIGNEES: list[str] = ROSTER["on_hold_assignees"]

# Sentinel strings — all team-specific literals live here, nowhere else.
ON_HOLD_STATUS: str = "On Hold"                   # Jira status name for on-hold tickets
ON_HOLD_SECTION: str = ON_HOLD_ASSIGNEES[0]       # sections dict key for the on-hold pool
ON_HOLD_GANTT_SECTION: str = "on_hold"            # Mermaid segment.section for the on-hold lane
UNASSIGNED_SENTINEL: str = "unassigned"           # fallback assignee for unknown/null Jira users
UNRESOLVABLE_NAMES: frozenset[str] = frozenset({"former user", "unassigned"})  # treated as unassigned
DEFAULT_TOPIC: str = "other"                      # fallback topic for unclassified tickets


def section_names_for_status(status: str) -> list[str]:
    """Return the section names (assignee pools) for a status bucket."""
    return ON_HOLD_ASSIGNEES if status == ON_HOLD_STATUS else MAIN_ASSIGNEES


# ── Factory functions ─────────────────────────────────────────────────────────

def topic_rules() -> list[TopicRule]:
    """Instantiate TopicRule objects from the TOPICS config."""
    return [TopicRule(**item) for item in TOPICS]


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
