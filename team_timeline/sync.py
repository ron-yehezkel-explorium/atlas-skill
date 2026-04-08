"""Merge Jira-fetched issues with local canonical ticket state.

Preserves local ordering, assignee overrides, and estimations.
Syncs title, status, labels, Type (Jira field), and last_synced from Jira.
"""

from __future__ import annotations

from .config import MAIN_ASSIGNEES, STATUSES, TIMEZONE
from .models import JiraIssue, Ticket, now_iso


def merge_tickets(
    existing: list[Ticket],
    fetched: dict[str, list[JiraIssue]],
) -> tuple[dict[str, dict[str, list[Ticket]]], dict[str, int]]:
    """Merge Jira issues with local ticket state.

    The canonical markdown file is the allowlist: only keys listed there are synced and
    written back. Jira issues not present locally are ignored (no auto-import).

    Strategy:
    - For each local ticket key, if Jira still has the issue: preserve assignee,
      estimation, parent_epic; update title, status, labels, jira_type (Type field), last_synced from Jira.
    - If the issue disappeared from Jira: drop it (counts as removed).
    - Local ordering is preserved; within each status/assignee bucket, Jira rank is used
      to interleave keys when the file order is incomplete.
    """
    synced_at = now_iso(TIMEZONE)
    existing_by_key = {t.key: t for t in existing}
    fetched_by_key = {issue.key: issue for status in STATUSES for issue in fetched[status]}
    merged: dict[str, Ticket] = {}

    for key, original in existing_by_key.items():
        issue = fetched_by_key.get(key)
        if issue is None:
            continue
        merged[key] = Ticket(
            key=key,
            title=issue.title,
            assignee=original.assignee,
            jira_type=issue.jira_type,
            status=issue.status,
            parent_epic=original.parent_epic,
            labels=issue.labels,
            estimation=original.estimation,
            last_synced=synced_at,
            group_status=issue.status,
            group_assignee=original.assignee,
        )

    removed_tickets = sum(1 for t in existing if t.key not in merged)

    # Rebuild ordered key lists: existing file order first, then Jira-rank inserts
    # for keys missing from the initial pass (normally none once allowlist-only).
    ordered: dict[str, dict[str, list[str]]] = {
        status: {section: [] for section in MAIN_ASSIGNEES}
        for status in STATUSES
    }
    for ticket in existing:
        if ticket.key not in merged:
            continue
        current = merged[ticket.key]
        ordered[current.status][current.assignee].append(ticket.key)

    for status in STATUSES:
        by_section: dict[str, list[str]] = {section: [] for section in MAIN_ASSIGNEES}
        for issue in fetched[status]:
            if issue.key not in merged:
                continue
            ticket = merged[issue.key]
            by_section[ticket.assignee].append(issue.key)
        for section, rank_keys in by_section.items():
            current = ordered[status][section][:]
            present = set(current)
            for idx, key in enumerate(rank_keys):
                if key in present:
                    continue
                insert_at = None
                for prev in reversed(rank_keys[:idx]):
                    if prev in present:
                        insert_at = current.index(prev) + 1
                        break
                if insert_at is None:
                    for nxt in rank_keys[idx + 1:]:
                        if nxt in present:
                            insert_at = current.index(nxt)
                            break
                if insert_at is None:
                    insert_at = len(current)
                current.insert(insert_at, key)
                present.add(key)
            ordered[status][section] = current

    materialized: dict[str, dict[str, list[Ticket]]] = {
        status: {section: [] for section in MAIN_ASSIGNEES}
        for status in STATUSES
    }
    for status in STATUSES:
        for section in MAIN_ASSIGNEES:
            for key in ordered[status][section]:
                ticket = merged[key]
                ticket.group_status = status
                ticket.group_assignee = section
                materialized[status][section].append(ticket)

    stats = {
        "synced_in_progress": sum(
            len(materialized["In Progress"][s]) for s in MAIN_ASSIGNEES
        ),
        "synced_to_do": sum(len(materialized["To Do"][s]) for s in MAIN_ASSIGNEES),
        "new_tickets": 0,
        "removed_tickets": removed_tickets,
        "auto_estimation_count": 0,
    }
    return materialized, stats
