# Jira Issue Creator (ATB)

Use this workflow when creating a new Jira issue so ticket content is consistent, readable, and actionable.

## Trigger
Any request to create/open/write a new Jira ticket/task/bug/issue.

## Write Permission Guard
- WRITE operations → **only** when user explicitly requests with words like "create", "open", "file", "add ticket"
- **Never** call Jira create/update tools until the user has given **explicit approval** (see [Approval before creation](#approval-before-creation)).
- "X is broken" → investigate only, do NOT create a ticket
- When unclear → default to READ

## Issue Type
Infer from context:
- **Bug** → error reports, broken behavior, regressions
- **Task** → implementation work, improvements, automation

Default: `Task`

## Board
Always `ATB`.

## Topic (MANDATORY)

Every ATB issue **must** have a Topic (`customfield_10264`, cascading select).

Allowed values (closed list — do not invent new ones):
| Value | Use when |
|---|---|
| Contacts | Contacts pipeline, prospects, person-level data |
| Data | Data pipelines, ingestion, quality, enrichment, EDS |
| Delivery | Customer delivery, exports, integrations |
| Firmo | Firmographic data, company-level attributes |
| Tech | Infrastructure, tooling, CI/CD, platform, frameworks |
| Other | Anything that doesn't fit the above categories |

**Selection rules:**
1. Infer from context (summary, description, related epic).
2. If ambiguous, ask the user before creating.
3. Never omit — the Jira create call will fail without it.

**API format** (inside `additional_fields`):
```json
{"customfield_10264": {"value": "<Topic>"}}
```

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

## Approval before creation

1. Decide every field value you will pass to the Jira create API (project, issue type, summary, full description with all sections, parent, assignee, priority, labels, components, or any other field the tool supports for this project).
2. **Before approval**, show **all** of those fields in one place, in plain text, using a fixed outline so nothing is implied or hidden:
   - List each field by name with its final value (or explicit `Omit` / `None` when the field is intentionally unset).
   - Include the full `description` body (Context, Motivation, DOD, optional Slack line)—not a summary of it.
   - If you are not setting a field that the create call could accept, still list it as `Omit` so the user sees the complete picture.
3. **Do not** call any Jira create or bulk-create tools until after step 2 is complete in the chat.
4. **Stop and wait** until the user explicitly approves creation. Accept only clear intent to proceed (e.g. “approve”, “yes create it”, “go ahead”, “looks good, create the ticket”). Do not infer approval from unrelated replies or from the initial “create a ticket” request alone.
5. If the user asks for edits, revise any affected fields, show the **full** field list again (step 2), then wait for approval again.
6. **Only after explicit approval** on the latest full field list (after any rounds of step 5) → use Atlassian MCP Jira create tools with exactly those approved values.

If the user declines or stops responding, do not create the issue.

Example shape for the pre-approval block (adjust fields to match the actual create payload):

```text
--- Fields to be created ---
project: ATB
type: Task
summary: ...
topic: Data | Contacts | Delivery | Firmo | Tech | Other   ← MANDATORY
description:
  [full text including Context / Motivation / DOD / optional Slack line]
parent: ATB-XXXX | Omit
assignee: ... | Omit
priority: ... | Omit
labels: ... | Omit
[any other fields]: ... | Omit
----------------------------
```

---

## Create Request

After [approval](#approval-before-creation), use Atlassian MCP Jira create tools (`atlassian_jira_*`) with these fields:

```text
project: ATB
type: Task
summary: Action-first short title
topic: Data                          ← MANDATORY, pass via additional_fields
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
additional_fields: {"customfield_10264": {"value": "Data"}}
```

`parent` is the epic connection. Omit if no epic applies.
`topic` is required — always include `customfield_10264` in `additional_fields`.
For bugs use `type: Bug`.

## Default Status

New tasks land in **Review** by default (board column configuration). Do NOT manually transition after creation — the board handles it.

---

## Verify

Use Atlassian MCP Jira view tools to verify `summary`, `parent`, `status` (should be `Review`), `customfield_10264` (Topic), and `description` on the created issue.
