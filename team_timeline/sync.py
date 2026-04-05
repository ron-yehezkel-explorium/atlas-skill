"""Merge Jira-fetched issues with local canonical ticket state.

Preserves local ordering, assignee overrides, topic overrides, and estimations.
Only syncs title, status, labels, and last_synced from Jira.
"""

from __future__ import annotations

from .config import (
    DEFAULT_TOPIC, ON_HOLD_SECTION, ON_HOLD_STATUS,
    STATUSES, TIMEZONE, UNASSIGNED_SENTINEL, section_names_for_status,
)
from .models import JiraIssue, Ticket, now_iso


def effective_section(ticket: Ticket) -> str:
    """Return the rendered section key for a ticket (shared for On Hold, else assignee)."""
    return ON_HOLD_SECTION if ticket.status == ON_HOLD_STATUS else ticket.assignee


def merge_tickets(
    existing: list[Ticket],
    fetched: dict[str, list[JiraIssue]],
) -> tuple[dict[str, dict[str, list[Ticket]]], dict[str, int]]:
    """Merge Jira issues with local ticket state.

    Strategy:
    - Existing tickets: preserve assignee, topic, estimation; update title, status, labels.
    - New tickets: ``topic`` = ``DEFAULT_TOPIC`` until edited in the tickets file; estimation=1.
    - Removed tickets (no longer in Jira): dropped silently.
    - Local file order is preserved for existing tickets; new tickets are inserted
      at the position nearest to their Jira rank neighbours.
    """
    synced_at = now_iso(TIMEZONE)
    existing_by_key = {t.key: t for t in existing}
    fetched_by_key = {issue.key: issue for status in STATUSES for issue in fetched[status]}
    merged: dict[str, Ticket] = {}

    new_tickets = 0
    auto_estimation_count = 0

    for key, issue in fetched_by_key.items():
        if key in existing_by_key:
            original = existing_by_key[key]
            merged[key] = Ticket(
                key=key,
                title=issue.title,
                assignee=original.assignee,
                topic=original.topic,
                status=issue.status,
                parent_epic=original.parent_epic,
                labels=issue.labels,
                estimation=original.estimation,
                last_synced=synced_at,
                group_status=issue.status,
                group_assignee=effective_section(original),
            )
        else:
            assignee = issue.assignee or UNASSIGNED_SENTINEL
            merged[key] = Ticket(
                key=key,
                title=issue.title,
                assignee=assignee,
                topic=DEFAULT_TOPIC,
                status=issue.status,
                parent_epic="",
                labels=issue.labels,
                estimation=1,
                last_synced=synced_at,
                group_status=issue.status,
                group_assignee=ON_HOLD_SECTION if issue.status == ON_HOLD_STATUS else assignee,
            )
            new_tickets += 1
            auto_estimation_count += 1

    removed_tickets = sum(1 for t in existing if t.key not in merged)

    # Rebuild ordered key lists: existing order first, then insert new tickets
    # at their Jira-rank-relative position within each section.
    ordered: dict[str, dict[str, list[str]]] = {
        status: {section: [] for section in section_names_for_status(status)}
        for status in STATUSES
    }
    for ticket in existing:
        if ticket.key not in merged:
            continue
        current = merged[ticket.key]
        ordered[current.status][effective_section(current)].append(ticket.key)

    for status in STATUSES:
        by_section: dict[str, list[str]] = {section: [] for section in section_names_for_status(status)}
        for issue in fetched[status]:
            ticket = merged[issue.key]
            by_section[effective_section(ticket)].append(issue.key)
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
        status: {section: [] for section in section_names_for_status(status)}
        for status in STATUSES
    }
    for status in STATUSES:
        for section in section_names_for_status(status):
            for key in ordered[status][section]:
                ticket = merged[key]
                ticket.group_status = status
                ticket.group_assignee = section
                materialized[status][section].append(ticket)

    stats = {
        "synced_in_progress": len(fetched["In Progress"]),
        "synced_to_do": len(fetched["To Do"]),
        "synced_on_hold": len(fetched[ON_HOLD_STATUS]),
        "new_tickets": new_tickets,
        "removed_tickets": removed_tickets,
        "auto_estimation_count": auto_estimation_count,
    }
    return materialized, stats
