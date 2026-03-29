# Workflow: Daily Team Brief

Goal: produce a compact, scannable daily document with per-person focus using Jira. Optimized for standup prep and risk/blocker radar.

**Performance target: under 3 minutes.**

## Defaults

Use defaults from your system prompt unless user overrides.

## Step 0: Time Window

Default: local start-of-day to now. Allow explicit `<start>` / `<end>` override.

## Step 1: Jira Data Collection

Use Atlassian MCP Jira tools (`atlassian_jira_*`). **Run ALL queries in parallel.**

### Query 1: In Progress per person

JQL:

```text
project = ATB AND assignee in (<team_emails>) AND status = "In Progress" AND issuetype in (Task, Bug) ORDER BY assignee ASC, priority DESC, updated DESC
```

### Query 2: Recently updated in window

JQL:

```text
project = ATB AND updated >= "<start>" AND updated <= "<end>" AND status = "In Progress" AND issuetype in (Task, Bug) ORDER BY updated DESC
```

### Query 3: Unassigned count only

JQL:

```text
project = ATB AND assignee is EMPTY AND statusCategory != Done AND issuetype in (Task, Bug) ORDER BY updated DESC
```

Count results only — do NOT enrich. Queries for Done transitions or Top To Do run only when explicitly requested.

## Step 2: Ticket Detail Enrichment

**Only enrich In Progress tickets** from Query 1. Run all enrichment calls in parallel batches.

For each ticket, fetch the issue details and comments via Atlassian MCP in parallel.

If a person has >10 in-progress tickets, enrich all but flag: `"⚠️ <Name> has <N> in-progress tickets — needs triage."`

## Step 3: Ranking (only when requested)

Only include Top To Do when user explicitly asks for "next priorities" / "top to do".

Rule (max 3 per person): issues not Done and not In Progress, sorted by priority desc → Bug before others → `updated` desc → key asc. Take first 3.

## Step 4: Output

**CRITICAL:** Every In Progress ticket MUST have the full ticket interior (What / State / Recent updates). Never collapse into summary paragraphs or bullet-point lists.

### Structure

```
# Daily Brief — <date>
---
## Attention Required
---
## Team Snapshot
---
## Per Person
### <Person> — <focus>
  ...repeated per person in roster order...
---
## Deep Dive
```

### Section 1: Attention Required

- Blocked tickets (who, how long, what unblocks)
- Active incidents / SEV tickets
- Unassigned count: `"N unassigned open tickets in ATB"`
- Hygiene: anyone with >10 in-progress tickets

Nothing? Write `None.`

### Section 2: Team Snapshot

```
| Person | Focus | In Progress | Blocked |
```

Focus = one-phrase theme from their tickets. Blocked = count or `—`.

### Section 3: Per Person

One section per person in roster order, separated by `---`.

```
### <Name> — <focus phrase>

**🔄 In Progress:**

<numbered tickets>
```

No in-progress tickets → `**🔄 In Progress:** none`

When Top To Do is requested, add after In Progress (numbering continues):

```
**📌 Top To Do:**

<numbered tickets>
```

#### Ticket Interior

```
N. **<KEY>** <Title> — **<flags if any>**

   **What:** <plain-English description, 1-6 lines>

   **State:** <blockers, progress, dependencies — omit if nothing to report>

   💬 **Recent updates:**
   > **<date>, <author>:** "<quoted comment>"
```

| Aspect | Rule |
|---|---|
| **What** | Always present. Adaptive length based on complexity. |
| **State** | Only when meaningful (blocked, % done, escalation). |
| **Flags** | Inline on title: **Blocked**, **SEV-N**. |
| **Recent updates** | Last 2-3 comments, most recent first. Omit entirely if none. |
| **Language** | Plain, direct. Missing data → `missing`. Always keep Jira keys. |

#### Emojis (strict — only these)

| Emoji | Where |
|---|---|
| 🔄 | In Progress label |
| 💬 | Recent updates label |
| 📌 | Top To Do label (when requested) |

### Section 4: Deep Dive

```
## Deep Dive

Want more context on any tickets? Reply with person + number:
> "Itai - 1, Yaara - 1 & 4"

I'll first explain deeper from Jira, then offer to research Slack, git, and Databricks for the full picture.

Need Top To Do sections? Just ask and I'll add next priorities for each person.
```

### Run Metadata

Mandatory block at the end:

```
---
**Run metadata:** generated_at=<ISO8601>, window=<start> → <end>, roster_source=system_prompt, in_progress_count=<N>, unassigned_count=<N>, enriched_count=<N>
```

Stale artifact detected (mtime or `generated_at` != today) → regenerate and warn: `"⚠️ Stale artifact detected — regenerated fresh."`

### Deep Dive Behavior (when user replies)

1. Full Jira deep dive (description, all comments, subtasks, linked issues, transitions).
2. Ask to expand. If yes: search Slack, git history, Databricks.
3. Synthesize findings.
