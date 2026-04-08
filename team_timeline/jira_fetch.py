"""Jira data fetching via acli.

All Jira I/O is isolated here. Nothing in this module writes to Jira.
"""

from __future__ import annotations

import base64
import concurrent.futures
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .config import DEFAULT_JIRA_TYPE, JIRA, ROSTER, STATUSES, UNASSIGNED_SENTINEL, UNRESOLVABLE_NAMES
from .models import JiraIssue, normalize_whitespace


# ── acli helpers ──────────────────────────────────────────────────────────────

def acli_json(command: list[str]) -> Any:
    """Run an acli command and parse its JSON stdout."""
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def _parse_type_field(raw: Any) -> str:
    """Jira single-select: ``{id, self, value}``; fall back to string or empty."""
    if raw is None:
        return DEFAULT_JIRA_TYPE
    if isinstance(raw, str):
        s = normalize_whitespace(raw)
        return s if s else DEFAULT_JIRA_TYPE
    if isinstance(raw, dict):
        v = raw.get("value")
        if v is not None and str(v).strip():
            return normalize_whitespace(str(v))
    return DEFAULT_JIRA_TYPE


def fetch_issue_type_value(key: str, field_id: str) -> str:
    """Read the Jira Type field via ``acli workitem view`` (fallback when search payload omits it)."""
    command = [
        "acli", "jira", "workitem", "view", key,
        "--fields", field_id,
        "--json",
    ]
    try:
        data = acli_json(command)
    except (subprocess.CalledProcessError, json.JSONDecodeError, TypeError):
        return DEFAULT_JIRA_TYPE
    if not isinstance(data, dict):
        return DEFAULT_JIRA_TYPE
    fields = data.get("fields") or {}
    return _parse_type_field(fields.get(field_id))


def enrich_keys_with_jira_type(keys: list[str], field_id: str) -> dict[str, str]:
    """Parallel ``view`` for each issue key missing Type on search; returns key → Type label."""
    if not keys:
        return {}
    unique = sorted(set(keys))
    out: dict[str, str] = {}

    def one(k: str) -> tuple[str, str]:
        return k, fetch_issue_type_value(k, field_id)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for k, v in ex.map(one, unique):
            out[k] = v
    return out


def _jira_basic_auth_header() -> str | None:
    email = (
        os.environ.get("JIRA_EMAIL")
        or os.environ.get("ATLASSIAN_USER_EMAIL")
        or os.environ.get("ATLASSIAN_EMAIL")
    )
    token = (
        os.environ.get("JIRA_API_KEY")
        or os.environ.get("JIRA_API_TOKEN")
        or os.environ.get("ATLASSIAN_API_TOKEN")
    )
    if not email or not token:
        return None
    raw = base64.b64encode(f"{email}:{token}".encode()).decode("ascii")
    return f"Basic {raw}"


def fetch_jira_type_labels_from_createmeta() -> list[str] | None:
    """Return all Type option labels in Jira field order via REST createmeta, or None if unavailable."""
    auth = _jira_basic_auth_header()
    if not auth:
        return None
    site = JIRA["site"].rstrip("/").replace("https://", "")
    project = urllib.parse.quote(JIRA["project"])
    itype = urllib.parse.quote(JIRA.get("createmeta_issue_type_id", "10157"))
    field_id = JIRA.get("type_field_id", "customfield_10264")
    url = (
        f"https://{site}/rest/api/3/issue/createmeta"
        f"?projectKeys={project}&issuetypeIds={itype}&expand=projects.issuetypes.fields"
    )
    req = urllib.request.Request(
        url,
        headers={"Authorization": auth, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    try:
        projects = payload.get("projects") or []
        if not projects:
            return None
        issuetypes = projects[0].get("issuetypes") or []
        if not issuetypes:
            return None
        fields = issuetypes[0].get("fields") or {}
        meta = fields.get(field_id) or {}
        allowed = meta.get("allowedValues") or []
        labels: list[str] = []
        for opt in allowed:
            if isinstance(opt, dict) and opt.get("value") is not None:
                labels.append(normalize_whitespace(str(opt["value"])))
            elif isinstance(opt, str):
                s = normalize_whitespace(opt)
                if s:
                    labels.append(s)
        return labels if labels else None
    except (KeyError, IndexError, TypeError):
        return None


def _jira_search_fields() -> str:
    """Include Type custom field in search so we can skip per-issue ``view`` when present."""
    s = JIRA["search_fields"]
    tid = (JIRA.get("type_field_id") or "").strip()
    if tid and tid not in s:
        return f"{s},{tid}"
    return s


def fetch_status_issues(status: str) -> list[dict[str, Any]]:
    """Fetch all issues with a given status from Jira via acli search."""
    command = [
        "acli", "jira", "workitem", "search",
        "--jql", JIRA["status_jql"][status],
        "--fields", _jira_search_fields(),
        "--limit", str(JIRA["search_page_size"]),
        "--paginate",
        "--json",
    ]
    try:
        return acli_json(command)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").lower()
        tid = (JIRA.get("type_field_id") or "").lower()
        if tid and f"field '{tid}' is not allowed" in stderr:
            fallback = [
                "acli", "jira", "workitem", "search",
                "--jql", JIRA["status_jql"][status],
                "--fields", JIRA["search_fields"],
                "--limit", str(JIRA["search_page_size"]),
                "--paginate",
                "--json",
            ]
            return acli_json(fallback)
        raise


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

def fetch_all_jira() -> tuple[dict[str, list[JiraIssue]], dict[str, int]]:
    """Fetch all tracked issues from Jira in parallel.

    Returns:
        issues_by_status: raw JiraIssue lists keyed by status (includes subtasks;
            use ``filter_issues`` to drop them)
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

    field_id = JIRA.get("type_field_id", "customfield_10264")
    type_by_key: dict[str, str] = {}
    keys_to_enrich: list[str] = []
    for status in STATUSES:
        for raw in raw_by_status.get(status, []):
            key = raw["key"]
            fields = raw.get("fields") or {}
            if field_id in fields:
                type_by_key[key] = _parse_type_field(fields.get(field_id))
            else:
                keys_to_enrich.append(key)
    type_by_key.update(enrich_keys_with_jira_type(sorted(set(keys_to_enrich)), field_id))

    for status in STATUSES:
        for raw in raw_by_status.get(status, []):
            fields = raw.get("fields") or {}
            issuetype = fields.get("issuetype") or {}
            issue_type = issuetype.get("name", "")
            is_st = issuetype.get("subtask", False) or is_subtask(issue_type)
            key = raw["key"]
            issue = JiraIssue(
                key=key,
                title=normalize_whitespace(str(fields.get("summary", ""))),
                assignee=resolve_assignee(fields.get("assignee")),
                status=(fields.get("status") or {}).get("name", status),
                issue_type=issue_type,
                labels=[str(item) for item in (fields.get("labels") or [])],
                is_subtask_issue=is_st,
                jira_type=type_by_key.get(key, DEFAULT_JIRA_TYPE),
            )
            issues_by_status[status].append(issue)

    stats = {
        "jira_calls": jira_calls,
        "jira_pages": jira_pages,
        "enrichment_calls": len(set(keys_to_enrich)),
        "jira_fetch_ms": int((time.time() - started) * 1000),
    }
    return issues_by_status, stats


def ordered_jira_type_labels(
    issues_by_status: dict[str, list[JiraIssue]],
    createmeta_labels: list[str] | None,
) -> list[str]:
    """Prefer full option list from createmeta; else distinct Type values from fetched issues (sorted)."""
    if createmeta_labels:
        return list(createmeta_labels)
    distinct: set[str] = set()
    for st in STATUSES:
        for issue in issues_by_status.get(st, []):
            distinct.add(issue.jira_type)
    return sorted(distinct)


def filter_issues(
    issues_by_status: dict[str, list[JiraIssue]],
) -> dict[str, list[JiraIssue]]:
    """Remove epics, subtasks, and out-of-roster assignees."""
    filtered = {status: [] for status in STATUSES}
    for status, issues in issues_by_status.items():
        for issue in issues:
            if issue.assignee is None:
                continue
            if is_epic(issue.issue_type):
                continue
            if issue.is_subtask_issue:
                continue
            filtered[status].append(issue)
    return filtered
