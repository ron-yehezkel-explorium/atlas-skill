# Jira Issue Creator (ATB)

Use this workflow when creating a new Jira issue so ticket content is consistent, readable, and actionable.

## Trigger
Any request to create/open/write a new Jira ticket/task/bug/issue.

## Write Permission Guard
- WRITE operations → **only** when user explicitly requests with words like "create", "open", "file", "add ticket"
- "X is broken" → investigate only, do NOT create a ticket
- When unclear → default to READ

## Issue Type
Infer from context:
- **Bug** → error reports, broken behavior, regressions
- **Task** → implementation work, improvements, automation

Default: `Task`

## Board
Always `ATB`.

## Priority
Set only if explicitly mentioned or obviously urgent. Otherwise omit.

## Ticket Linking
Every ticket ID in output must be a clickable link: `[ATB-123](https://exploriumai.atlassian.net/browse/ATB-123)`  
Never write bare IDs. Never use backticks around ticket IDs.

---

## Content Format

Plain text only in `--description`. No ADF JSON. Fixed sections in this order:

```text
Context

[Comprehensive background about systems, dependencies, requirements. Include technical details, architecture notes, or business context that helps understand why this work is needed.]

Motivation

[Business value, user impact, or technical debt being addressed. Connect to team goals or user pain points. Be specific about what problem this solves or what opportunity it creates.]

DOD

- Functional requirements
- Testing requirements
- Documentation needs
- Deployment considerations
- Success metrics (if applicable)

Requested via Slack: <permalink>   ← include only when a Slack link is available
```

---

## Create Request

Use Atlassian MCP Jira create tools (`atlassian_jira_*`) with these fields:

```text
project: ATB
type: Task
summary: Action-first short title
description: Context

...

Motivation

...

DOD

- ...
- ...

Requested via Slack: https://goldinai.slack.com/archives/CHANNEL/pTIMESTAMP
parent: ATB-XXXX
assignee: @me
```

`parent` is the epic connection. Omit if no epic applies.
For bugs use `type: Bug`.

## Default Status

New tasks land in **Review** by default (board column configuration). Do NOT manually transition after creation — the board handles it.

---

## Verify

Use Atlassian MCP Jira view tools to verify `summary`, `parent`, `status` (should be `Review`), and `description` on the created issue.
