"""Jira data fetching via acli.

All Jira I/O is isolated here. Nothing in this module writes to Jira.
"""

from __future__ import annotations

import concurrent.futures
import json
import subprocess
import time
from typing import Any

from .config import JIRA, ON_HOLD_STATUS, ROSTER, STATUSES, UNASSIGNED_SENTINEL, UNRESOLVABLE_NAMES
from .models import JiraIssue, normalize_whitespace


# ── acli helpers ──────────────────────────────────────────────────────────────

def acli_json(command: list[str]) -> Any:
    """Run an acli command and parse its JSON stdout."""
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def fetch_status_issues(status: str) -> list[dict[str, Any]]:
    """Fetch all issues with a given status from Jira via acli search."""
    command = [
        "acli", "jira", "workitem", "search",
        "--jql", JIRA["status_jql"][status],
        "--fields", JIRA["search_fields"],
        "--limit", str(JIRA["search_page_size"]),
        "--paginate",
        "--json",
    ]
    return acli_json(command)


def fetch_parent_keys_for_subtasks(subtask_keys: list[str]) -> set[str]:
    """Return the parent keys of the given subtasks.

    Uses targeted workitem view calls — only invoked for the small set of
    subtasks found in tracked statuses, keeping total Jira calls low.
    """
    parent_keys: set[str] = set()
    for key in subtask_keys:
        try:
            detail = acli_json(["acli", "jira", "workitem", "view", key, "--fields", "key,parent", "--json"])
            parent = (detail.get("fields") or {}).get("parent") or {}
            if parent.get("key"):
                parent_keys.add(parent["key"])
        except Exception as exc:
            print(f"[warn] failed to resolve parent for subtask {key}: {exc}")
    return parent_keys


# ── Issue parsing ─────────────────────────────────────────────────────────────

def resolve_assignee(raw: Any) -> str | None:
    """Map a raw Jira assignee field to a canonical roster key.

    Returns None if the assignee cannot be matched to any roster member
    (i.e. someone outside the team). Returns "unassigned" for empty/null.
    """
    if not raw:
        return UNASSIGNED_SENTINEL
    candidates = [raw] if isinstance(raw, str) else [
        raw.get("emailAddress"), raw.get("displayName"),
        raw.get("email"), raw.get("display_name"), raw.get("name"),
    ]
    lowered = [normalize_whitespace(str(item).lower()) for item in candidates if item]
    if not lowered:
        return UNASSIGNED_SENTINEL
    if any(item in UNRESOLVABLE_NAMES for item in lowered):
        return UNASSIGNED_SENTINEL
    for key, variants in ROSTER["aliases"].items():
        if any(item in variants or item == key or item.startswith(f"{key}.") for item in lowered):
            return key
    return None


def is_epic(issue_type: str) -> bool:
    return issue_type.lower() == "epic"


def is_subtask(issue_type: str) -> bool:
    return issue_type.lower().replace("-", "") == "subtask"


# ── Main fetch entry point ────────────────────────────────────────────────────

def fetch_all_jira() -> tuple[dict[str, list[JiraIssue]], set[str], dict[str, int]]:
    """Fetch all tracked issues from Jira in parallel, then resolve subtask parents.

    Returns:
        issues_by_status: raw JiraIssue lists keyed by status
        parent_keys_with_subtasks: parent issue keys that have at least one subtask
        stats: timing and call-count metrics
    """
    started = time.time()
    raw_by_status: dict[str, list[dict[str, Any]]] = {}
    jira_calls = 0
    jira_pages = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fetch_status_issues, status): status for status in STATUSES}
        for future in concurrent.futures.as_completed(futures):
            status = futures[future]
            items = future.result()
            raw_by_status[status] = items
            jira_calls += 1
            jira_pages += max(1, (len(items) + JIRA["search_page_size"] - 1) // JIRA["search_page_size"])

    issues_by_status: dict[str, list[JiraIssue]] = {status: [] for status in STATUSES}
    subtask_keys: list[str] = []

    for status in STATUSES:
        for raw in raw_by_status.get(status, []):
            fields = raw.get("fields") or {}
            issuetype = fields.get("issuetype") or {}
            issue_type = issuetype.get("name", "")
            is_sub = issuetype.get("subtask", False) or is_subtask(issue_type)
            issue = JiraIssue(
                key=raw["key"],
                title=normalize_whitespace(str(fields.get("summary", ""))),
                assignee=resolve_assignee(fields.get("assignee")),
                status=(fields.get("status") or {}).get("name", status),
                issue_type=issue_type,
                labels=[str(item) for item in (fields.get("labels") or [])],
            )
            issues_by_status[status].append(issue)
            if is_sub:
                subtask_keys.append(raw["key"])

    parent_keys_with_subtasks = fetch_parent_keys_for_subtasks(subtask_keys)
    jira_calls += len(subtask_keys)

    stats = {
        "jira_calls": jira_calls,
        "jira_pages": jira_pages,
        "enrichment_calls": len(subtask_keys),
        "jira_fetch_ms": int((time.time() - started) * 1000),
    }
    return issues_by_status, parent_keys_with_subtasks, stats


def filter_issues(
    issues_by_status: dict[str, list[JiraIssue]],
    parent_keys_with_subtasks: set[str],
) -> dict[str, list[JiraIssue]]:
    """Remove epics, parent-of-subtask issues, and out-of-roster assignees.

    On Hold tickets are kept regardless of assignee — they go into the shared pool.
    """
    filtered = {status: [] for status in STATUSES}
    for status, issues in issues_by_status.items():
        for issue in issues:
            if status != ON_HOLD_STATUS and issue.assignee is None:
                continue
            if is_epic(issue.issue_type):
                continue
            if issue.key in parent_keys_with_subtasks and not is_subtask(issue.issue_type):
                continue
            filtered[status].append(issue)
    return filtered
