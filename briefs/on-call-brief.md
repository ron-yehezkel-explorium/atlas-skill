# Workflow: On-Call Brief

Goal: scan channels where @atlas-oncall is active, analyze issues in the requested time window, and produce a compact handoff brief.

## Defaults

Use defaults from your system prompt unless user overrides.

- On-call usergroup ID: `S0227A6C3BQ` (`@atlas-oncall`)
- On-call person’s Slack user ID: resolve from the team roster (`slack_user_id` for whoever is on-call in Step 1). Example: `U088JLP938B` (`@ron.yehezkel`).
- On-call rotation channel: `C04DKFGBQNR` (`#atlas-internal`)
- Databricks warehouse ID: `2dfc33368ea84f86`

## Step 0: Time Window

Default: 3 days back (start-of-day) to now. Allow explicit `<start>` / `<end>` override.

## Step 1: Identify Current On-Call

Query `#atlas-internal` for the latest GMinion rotation update.

## Step 2: Channel Discovery

Run in parallel:

**Seed channels (always scan):**

| Channel | ID |
|---|---|
| #issues-data | C011J4X9414 |
| #data-incidents | resolve at runtime |
| #get-support | C0268LQHAJ0 |
| #alerts-events-generation | resolve at runtime |
| #alerts-tube | C04EP149U73 |
| #atlas-dpd-public | resolve at runtime |

**Dynamic discovery:** Search Slack for messages mentioning `S0227A6C3BQ` in the time window. Merge with seed list and deduplicate.

## Step 2b: Personal mentions (all channels)

Independently of Steps 2–3, run a **workspace-wide** Slack search in the same time window for messages that **@mention the current on-call person** (their `slack_user_id` from the roster, e.g. `<@U088JLP938B>` in search queries).

- **Scope:** all channels the token can search — not limited to the seed list or to `@atlas-oncall` traffic.
- **Include** root posts and thread replies where the mention appears.
- **Deduplicate** by `(channel, thread_ts or message ts)`; if the same thread hits multiple times, keep one row (latest relevant activity or the message that contains the mention).
- **Permalink** each row (same format as Step 3).

This feed is for the **Tagged me** table in the output only. It does not replace the Issues relevance gate: Issues still follow Step 3 rules for `@atlas-oncall` / seed alerts.

## Step 3: Message Collection

For each channel: fetch messages in the time window and **all thread replies**.

**Relevance gate — include if EITHER condition is met:**

1. **Human tag:** `@atlas-oncall` was explicitly tagged by a human in the root or any reply.
2. **Automated alert (seed channels only):** Bot/webhook message — but exclude GMinion auto-responses without a human `@atlas-oncall` tag.

Drop everything else.

**Permalink requirement:** For every collected root message, construct the Slack permalink:

```
https://exploriumai.slack.com/archives/<CHANNEL_ID>/p<ts_without_dot>
```

Example: channel `C011J4X9414`, ts `1709472135.123456` → `https://exploriumai.slack.com/archives/C011J4X9414/p1709472135123456`

Store this permalink — it is **mandatory** in the output card. If you cannot construct it, note `[link unavailable]` but never omit the field.

## Step 4: Issue Extraction & Deduplication

Treat each unique incident as one issue. Collapse recurring alerts into a single issue with `(xN)` count.

For each issue derive **ALL** of the following — every field is **mandatory** (use `unknown`, `unassigned`, or `None` when data is unavailable, but never omit a field):

| Field | Description |
|---|---|
| **title** | Short descriptive title |
| **slack_link** | Slack permalink to root message (from Step 3) |
| **summary** | 1-2 sentence plain-English description of what happened, based on the message content and thread replies |
| **source** | `automated` or `human` |
| **status** | `open` / `investigating` / `known` / `resolved` / `auto-recovered` / `unknown` |
| **when** | Full date + time: `Mon DD, HH:MM AM/PM` |
| **channel** | `#channel-name` |
| **triggered_by** | Person name or bot name that posted the root message |
| **owner** | Who is handling it (from replies), else `unassigned` |
| **response** | First on-call reply: who + when + what they said (1 line). If none: `None` |
| **jira** | Ticket key(s) if found, else omit |
| **needed** | Actionable next step (open/investigating only) |

Status rules:
- Look for explicit signals in replies (emoji, "fixed", "resolved", "merged", "deployed", "looking into it").
- Cross-reference Jira status (Step 4.5). No evidence → `unknown`.

**You MUST read thread replies** (`conversations_replies`) for every collected message to populate `summary`, `owner`, `response`, and `status` accurately. Do not guess these from the root message alone.

## Step 4.5: Jira Enrichment

Scan messages for Jira ticket patterns (`ATB-\d+`, `ES-\d+`, `ST-\d+`, `[A-Z]{2,}-\d+`) or `atlassian.net/browse/<KEY>` URLs.

Use Atlassian MCP Jira tools (`atlassian_jira_*`). For each ticket, fetch the issue details and comments in parallel.

Jira `Done`/`Resolved` → issue status `resolved`. Jira `In Progress` → issue status `investigating`. Always keep Jira key in output.

## Step 4.6: Databricks Investigation

Triggered when an issue references Databricks (URLs with `databricks.com/jobs/`, keywords like `job failed`, `workflow failed`, `ETL`, `pipeline failed`, `tube_catalog`, `tube_bronze`, `DBT`).

Load `databricks-sql` skill. Warehouse ID: `2dfc33368ea84f86`.

- **Job ID present:** `databricks jobs list-runs --job-id <JOB_ID> --limit 5 --output json`
- **Data freshness issue:** query `SELECT MAX(partition_date), COUNT(*) FROM <table> LIMIT 1`
- **Run failure:** `databricks jobs get-run --run-id <RUN_ID> --output json`

Add findings to the issue description.

## Step 5: Output

### Structure

```
# On-Call Brief — <date or range>
**On-Call:** <name> (since <date>, rotation ends <date>)
---
## Issues
<numbered stacked cards — open first, then resolved>
---
## Tagged me (all channels)
<table from Step 2b only — see below>
---
## Deep Dive
```

### Issue Cards

Sorted: open/investigating/known first (🔴/🟡), then resolved (✅). Most recent first within each group.

**Open / Investigating / Known:**

```
**N. <Issue title>** [+ (xN)] — <emoji + label> — [Slack](<permalink>)
**Summary:** <1-2 sentence plain-English description of what happened>
**When:** <Mon DD, HH:MM AM/PM>
**Channel:** #<channel>
**Triggered by:** <name or bot>
**Owner:** <person handling it> | `unassigned`
**Response:** <who> (<Mon DD, HH:MM AM/PM>) — <what they did, one line> | or `None`
**Jira:** <KEY> | omit if none
**Needed:** <actionable next step>
```

**Resolved / Auto-recovered:** Same format but omit **Needed**.

---

### ⛔ Output Format Enforcement

**Every issue MUST be rendered as a full multi-line card.** Single-line bullet summaries are **NOT acceptable**.

❌ **BAD — DO NOT DO THIS:**
```
- 1) Emlite DPD failures (match_prospect) — 🔴 Open (#issues-data, Mar 3 09:22 PM)
- 2) Daily Enrichments tests failing — 🟡 Investigating (#issues-data, Mar 3 10:21 AM)
```

✅ **GOOD — THIS IS THE REQUIRED FORMAT:**
```
**1. Emlite DPD failures (match_prospect, google_news_genai)** — 🔴 Open — [Slack](https://exploriumai.slack.com/archives/C011J4X9414/p1709472135123456)
**Summary:** DPD enrichment pipeline failing for match_prospect and google_news_genai providers; jobs erroring out with timeout exceptions during entity resolution.
**When:** Mar 3, 07:22 PM
**Channel:** #issues-data
**Triggered by:** DPD Alert Bot
**Owner:** Itai Dagan
**Response:** Itai Dagan (Mar 3, 07:45 PM) — acknowledged, restarting failed jobs and checking provider health
**Needed:** Confirm providers are healthy after restart; escalate if failures recur within 2 hours
```

If you produce single-line bullets instead of full cards, your output is **invalid**. Go back and re-render.

**Every card MUST include ALL of:** Slack permalink, Summary, When, Channel, Triggered by, Owner, Response. A card missing any of these is invalid — go back and fetch the data.

### Tagged me (all channels)

A **markdown table** built **only** from Step 2b (personal `@` mentions of the on-call person across the workspace). Do not mix in Issues-only rows unless that row also had a personal mention.

| When | Channel | Summary | Slack |
|---|---|---|---|
| `<Mon DD, HH:MM AM/PM>` | `#channel` | One short line: what the thread is about | `[link](<permalink>)` |

- Sort **most recent first**.
- If there were no personal mentions in the window, output the section header and a single line: `None in this window.`

### Status Emojis

| Emoji | Status |
|---|---|
| 🔴 | Open |
| 🟡 | Investigating / Known |
| ✅ | Resolved / Auto-recovered |

### Content Rules

- **When**: full date + time (`Feb 27, 02:15 AM`).
- **Response**: if none, just `None`. Include Jira keys inline where relevant.
- **Recurring alerts**: collapse into one card with `(xN)`.
- **Links**: clickable Slack/Datadog/Databricks links on title line.
- **Language**: plain, direct. Unknown status → `unknown`.

### Deep Dive

```
## Deep Dive

Want more context? Reply with issue number:
> "1" or "1, 2"

I'll dig deeper into Jira, Slack threads, Databricks, and git for the full picture.
```

**When user replies:**
1. Show full Slack thread + all Jira details.
2. Ask to expand. If yes: search Slack for related threads, git history for commits/PRs, Databricks for pipeline data.
3. Synthesize findings.
