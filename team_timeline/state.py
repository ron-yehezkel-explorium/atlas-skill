"""Read and write the canonical local ticket state file (team-timeline-tickets.md)."""

from __future__ import annotations

import json
from pathlib import Path

from .config import DEFAULT_JIRA_TYPE, MAIN_ASSIGNEES, STATUSES, UNASSIGNED_SENTINEL
from .models import Ticket

def parse_tickets_markdown(path: Path) -> list[Ticket]:
    """Parse the canonical tickets markdown into a flat ordered list of Tickets."""
    if not path.is_file():
        return []
    lines = path.read_text().splitlines()
    tickets: list[Ticket] = []
    status = ""
    assignee = ""
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("## "):
            heading = line[3:].strip()
            if heading in STATUSES:
                status = heading
            i += 1
            continue
        if line.startswith("### "):
            assignee = line[4:].strip()
            i += 1
            continue
        if line.startswith("- key: "):
            block: dict[str, str] = {"key": line.split(":", 1)[1].strip()}
            i += 1
            while i < len(lines) and lines[i].startswith("  "):
                field_line = lines[i].strip()
                if ":" in field_line:
                    k, v = field_line.split(":", 1)
                    block[k.strip()] = v.strip()
                i += 1
            raw_type = block.get("type")
            tickets.append(Ticket(
                key=block["key"],
                title=block.get("title", ""),
                assignee=block.get("assignee", UNASSIGNED_SENTINEL),
                jira_type=raw_type if raw_type else DEFAULT_JIRA_TYPE,
                status=block.get("status", status),
                parent_epic=block.get("parent_epic", ""),
                labels=json.loads(block.get("labels", "[]") or "[]"),
                estimation=int(block.get("estimation", "1") or 1),
                last_synced=block.get("last_synced", ""),
                group_status=status,
                group_assignee=assignee,
            ))
            continue
        i += 1
    return tickets


def sections_from_flat_tickets(tickets: list[Ticket]) -> dict[str, dict[str, list[Ticket]]]:
    """Rebuild merge-shaped sections from a flat parse (file order preserved per bucket)."""
    sections: dict[str, dict[str, list[Ticket]]] = {
        status: {name: [] for name in MAIN_ASSIGNEES}
        for status in STATUSES
    }
    for t in tickets:
        st = t.group_status
        if st not in sections:
            continue
        sec = t.group_assignee
        if sec not in sections[st]:
            continue
        sections[st][sec].append(t)
    return sections



def render_tickets_markdown(
    sections: dict[str, dict[str, list[Ticket]]],
) -> str:
    """Serialise the merged ticket sections back to the canonical markdown format."""
    lines = [
        "# Team Timeline Tickets",
        "",
        "Canonical local state for team timeline sync.",
        "",
    ]
    for status in STATUSES:
        lines.extend([f"## {status}", ""])
        for section in MAIN_ASSIGNEES:
            lines.extend([f"### {section}", ""])
            for ticket in sections[status][section]:
                lines.extend([
                    f"- key: {ticket.key}",
                    f"  title: {ticket.title}",
                    f"  assignee: {ticket.assignee}",
                    f"  type: {ticket.jira_type}",
                    f"  status: {ticket.status}",
                    f"  parent_epic: {ticket.parent_epic}",
                    f"  labels: {json.dumps(ticket.labels, ensure_ascii=False)}",
                    f"  estimation: {ticket.estimation}",
                    f"  last_synced: {ticket.last_synced}",
                    "",
                ])
    return "\n".join(lines).rstrip() + "\n"
