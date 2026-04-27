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
| Oncall | oncall issues OR CS/customer-facing analysis tickets routed through on-call |
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

## CS Analysis Ticket Flow

Use this flow when the user explicitly asks to create/open/file/add a **CS ticket**, **CS analysis ticket**, or customer-facing analysis ticket. Common sources are `#data-requests`, `#data-public`, customer channels, or Slack threads from CS/revenue users, but those are signals only — do not require a specific channel or requester.

This flow overrides the generic ticket defaults below. It is still a Jira write flow: **show the full preflight fields and wait for explicit approval before creating anything**.

### CS Field Rules

- `project`: `ATB`
- `type`: `Task` unless the request is clearly a bug/regression
- `summary`: start with `[cs]`
- `topic`: `oncall`, passed as `customfield_10264`
- `labels`: always include `gminion`, plus approved customer label(s) when inferred
- `requester/reporter`: the employee who found/reported the issue in the Slack thread, not necessarily the person asking to create the ticket
- `assignee`: current Atlas on-call
- `status`: transition to `To Do` after creation
- `rank`: rank at the top of `To Do` when a ranking tool/API is available; if not available, explicitly say ranking was not performed
- `source`: validated Slack permalink when the request came from Slack

### CS Field Inference

1. Infer customer names from channel name, request text, thread history, and examples.
2. Canonicalize customer labels before creation when possible:
   - Compare by a normalized key that lowercases and removes spaces, `_`, `-`, `.`, and `/`.
   - Reuse an existing Jira label when the normalized key matches.
   - Only create a new customer label when no equivalent existing label is found.
   - If label lookup is unavailable, show the inferred label(s) in the preflight and wait for approval.
3. Infer the requester/reporter from the original issue report in the Slack thread. If unclear, show `Requester: unclear` and ask for correction.
4. Identify the current Atlas on-call by checking the latest rotation update in `#atlas-internal`, then map the Slack user to the team roster. If unclear, ask before creation.

### CS Preflight Fields

Before creation, show all final fields in one plain-text block:

```text
--- CS ticket fields to be created ---
project: ATB
type: Task | Bug
summary: [cs] ...
topic: oncall
labels: gminion[, <customer_label>...]
customer labels: <labels> | none inferred
requester/reporter: <employee> | unclear
assignee: <current Atlas on-call>
status after create: To Do
rank: top of To Do when available | Not available
description:
  [full text using the CS description template]
parent: ATB-XXXX | Omit
priority: ... | Omit
components: ... | Omit
additional_fields: {"customfield_10264":{"value":"oncall"},"labels":["gminion",...]}
--------------------------------------
```

Stop after showing the block. Create only after explicit approval such as `approve`, `yes create`, `go ahead`, or `looks good, create it`.

### CS Description Template

Plain text only:

```text
Context

[Slack/request background, customer, data/product area, relevant examples]

Analysis request

[The question/problem to analyze]

Customer

[Customer name(s), or Not inferred]

Requester

[Employee who found and reported the issue]

Evidence / examples

- [IDs, domains, screenshots/files mentioned, exact examples]

Expected output

[What answer/artifact CS needs, or Atlas analysis and recommendation]

Source

Requested via Slack: <permalink>

DOD

- Investigate the examples and identify root cause or explain limitation
- Share findings and recommended next step in the Jira ticket
- Update the CS-facing Slack thread with a concise summary when done
```

### CS Create Request

After approval:

1. Create the ATB issue using the approved fields.
2. Include `customfield_10264` with `oncall` in `additional_fields`.
3. Include `labels` with `gminion` and any approved customer labels in `additional_fields`.
4. Set the Jira reporter/requester to the approved employee when Jira permissions allow it. If Jira rejects reporter changes, keep the created reporter and preserve the approved requester in the description.
5. Assign the ticket to the current Atlas on-call.
6. Transition the ticket to `To Do` using `atlassian_jira_get_transitions` then `atlassian_jira_transition_issue`.
7. Rank the ticket at the top of `To Do` when a ranking tool/API is available. If ranking fails or is unavailable, still report the created ticket and explicitly state the ranking result.

### CS Verify

Use Atlassian MCP Jira view tools to verify `summary`, `labels`, `assignee`, `reporter` when set, `status` (`To Do`), `customfield_10264` (`oncall`), and `description`.

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

Requested via Slack: https://<workspace>.slack.com/archives/<CHANNEL_ID>/p<TS_NO_DOT>
parent: ATB-XXXX
assignee: @me
additional_fields: {"customfield_10264": {"value": "Data"}}
```

`parent` is the epic connection. Omit if no epic applies.
`topic` is required — always include `customfield_10264` in `additional_fields`.
For bugs use `type: Bug`.
If the task came from Slack, preserve the exact host from the user-pasted Slack link when one exists. If you have to construct the link yourself, use the runtime default workspace URL, prefer `thread_ts` over a reply `ts`, and validate it with `slack_conversations_search_messages` before writing it into the Jira description.

## Default Status

New tasks land in **Review** by default (board column configuration). Do NOT manually transition after creation — the board handles it.

---

## Verify

Use Atlassian MCP Jira view tools to verify `summary`, `parent`, `status` (should be `Review`), `customfield_10264` (Topic), and `description` on the created issue.
