# Workflow: Slack Discussion Analyzer

Goal: fetch a Slack thread from a pasted link, explain what it is about in simple English, investigate only as much as needed, then execute the user's requested action (formulate a response, summarize, investigate, etc.).

## Core Principles

1. **Short answer first.** Start with 2-3 short paragraphs explaining what the thread is about, what the issue is, which components matter, and the best current explanation.
2. **Investigate only as needed.** Use Slack + local repos + git/Jira first. Use Databricks, Datadog, and GitHub only when they are needed to answer the core question.
3. **Data requires samples.** If Databricks or another data source is used, show a small sample of actual data/output, not just table names or schemas.
4. **Avoid redundant structure.** Do not output metadata tables, key-example tables, or timelines unless they add new information.

## Step 0: Parse the Slack Link

Extract channel ID and message timestamp from the permalink.

**Format:** `https://<workspace>.slack.com/archives/<CHANNEL_ID>/p<TS_NO_DOT>`

The workspace subdomain varies (e.g., `goldinai`) — do not hardcode a different host. Preserve the host from the user's pasted link exactly.

**Parsing rule:** strip `p` prefix, insert `.` before the last 6 digits → Slack API `ts`.

Example: `https://goldinai.slack.com/archives/C011J4X9414/p1709472135123456`
→ channel = `C011J4X9414`, ts = `1709472135.123456`

If the link doesn't match the expected format, ask the user to re-paste it.

If you need to reconstruct a permalink for output, use the thread root timestamp (`thread_ts` if present, otherwise message `ts`) so the link opens the correct thread.

## Step 1: Fetch the Discussion

Use Slack MCP tools. Run these in parallel:

1. **Thread replies** — `slack_conversations_replies` with the parsed `channel_id` and `thread_ts`. Set `limit` to `90d` to capture the full thread.
2. **Channel name** — Use `slack_conversations_search_messages` with the original Slack permalink URL as the `search_query`. This returns a single message with the `#channel-name` in the `Channel` column — the most reliable method. **Fallback:** if the search returns nothing, try `slack_channels_list` or use the raw channel ID.

Treat `slack_conversations_search_messages(search_query=<permalink>)` as the permalink validation step too. If a generated or repaired permalink does not resolve, rebuild it from the thread root timestamp and retry once before showing it to the user.

If `slack_conversations_replies` returns nothing or only one message, the link may point to a standalone message (no thread). In that case, present what's available and note: `"This is a standalone message, not a threaded discussion."`

### File Attachments

Messages may include file attachments (indicated by `FileCount > 0` in the CSV). Note file counts in the timeline but do not attempt to download them — flag them for manual review if they seem relevant to the discussion.

## Step 2: Resolve Participants

Cross-reference Slack user IDs from the messages against the team roster in your system prompt. For known team members, use their name and role.

For unknown users who appear as **message authors** in the thread CSV, resolve via `slack_users_search` using the display name or username from the CSV. Batch all unknown user lookups in parallel.

For user IDs that only appear in **@mentions** (not as message authors), the CSV doesn't provide a display name. `slack_users_search` cannot look up raw Slack user IDs directly. Flag these as `(unresolved)` in the digest rather than making failing lookups.

Display format: `**Name** (role if known)` for team members, `**Display Name**` for external/unknown, `U0XXXXXXXX (unresolved)` for mention-only IDs that couldn't be resolved.

## Step 3: Build the Short Explanation

Start with a short plain-English explanation. This is the main answer unless the user asked for a deeper investigation.

Cover:
- what the discussion is about
- what the actual issue/question is
- which customer/component/system is involved
- the best current explanation, clearly marked as confirmed or hypothesis

Rules:
- Keep this to 2-3 short paragraphs.
- Explain components as if the reader has no project context.
- Preserve exact error text, IDs, links, and file references only when they matter.
- Flag unresolved questions and clear action items.
- Echo the original validated permalink if showing the link.

### Normalize Slack Evidence Before Writing

Before building the brief, normalize noisy Slack content:

- Detect forwarded/copied Slack snippets such as `Author: ...`, `Text: ...`, `Footer: ...` and restate them as normal evidence.
- Separate **thread authors** from **mentioned users**.
- Extract concrete artifacts when present: customer names, IDs, URLs, repo names, service names, job IDs, table names, Jira tickets, timestamps, errors.
- For tiny threads (2-4 messages), avoid outputting a full timeline unless the timing itself matters.

## Step 3b: Decide Whether to Investigate More

After the short explanation, investigate only if the thread cannot be answered confidently or the user asked for it.

Default order:
1. Slack thread evidence
2. local repos and git history
3. Jira / PR context
4. Databricks only when production data is required
5. Datadog only for runtime/log/incident questions
6. GitHub only when local repo evidence is insufficient

### Databricks gate

Use Databricks only when the core unresolved question is about actual data state: IDs, rows, counts, batch output, customer delivery files, or production validation. If Databricks is not clearly required, stop after the explanation and offer: `I can validate this in Databricks next if you want.`

When Databricks is used, always include:
- what table/model/job was checked
- what it is in simple English
- the query or inspection method
- a small sample of the actual data/output

## Step 4: Write the Conclusion

If deeper investigation was performed, add a short conclusion covering what was confirmed, what is still uncertain, the best explanation, and the next action. Do not repeat the thread.

## Step 4b: Offer Follow-up Options

After a successful analysis of the full thread, always offer exactly three ways to continue and recommend the best one for this case.

```
## Suggested Next Step

I recommend: <Option 1/2/3> — <one short reason>

Choose one:
1. **Simple Slack response** — draft a concise reply Ron can paste back into Slack.
2. **Deep check with tools** — continue investigating with targeted tools such as Jira, other Slack channels, local repos/git, Datadog logs, and Databricks queries when needed.
3. **Heavy Databricks notebook investigation** — run a longer full analysis, create a Databricks notebook with read-only queries and evidence, then return a summary plus notebook link so Ron can inspect and continue manually in Databricks.
```

Recommendation rules:
- Recommend **Option 1** when the thread is mostly coordination, status, or a simple answer is enough.
- Recommend **Option 2** when there is a real unresolved technical question but it can likely be answered with targeted checks.
- Recommend **Option 3** only for complex data investigations that need repeatable SQL, multiple samples, historical comparisons, or a handoff artifact in Databricks.
- Do not run Options 2 or 3 unless the user chooses them or explicitly asks for deeper validation.
- Option 3 must use read-only Databricks operations only.

## Step 5: Execute the Requested Action

The user will specify what they need. Match intent and execute:

| Intent | Behavior |
|---|---|
| **Formulate a response / reply** | Draft a reply matching Ron's tone (direct, technical, concise). Provide 1-2 variants if the situation is nuanced. Include relevant context from Jira/git if the discussion references tickets or code. |
| **Understand / summarize** | Start with a `### Simple Explanation` section in plain language: 3-5 short sentences, minimal jargon, answer only `what happened`, `why it matters`, and `whether this looks like a new breakage or an existing gap`. Then provide the structured summary: what's being discussed, key positions, unresolved points, and any decisions made. |
| **Investigate / solve** | Identify the technical problem from the thread. Search local repos (`git log`, code), Jira (Atlassian MCP), and Databricks if relevant. Propose a solution with evidence. |
| **Draft an update** | Compose a status update or follow-up message based on the thread context and any new information from Jira/git. |
| **Identify action items** | Extract all explicit and implicit action items, assign owners where clear, flag unowned items. |
| **Heavy Databricks notebook investigation** | Create a read-only Databricks notebook that runs the full analysis with queries, samples, and explanation. Return a short summary and the notebook link. |

If the intent is unclear, present the brief (Step 3), investigation (Step 3b), and analysis summary (Step 4), then ask: `"What would you like me to do with this discussion?"` with the options above.

## Step 5b: Bare Link — Deep Investigation

When the user pastes **only a Slack link with no additional text**, treat it as: "explain this thread and do a reasonable first-pass investigation." Do not automatically run every tool.

After Step 3, inspect local repo/git/Jira only if the thread references a technical component, customer issue, ticket, deploy, or data artifact. Use Databricks/Datadog only if gated by Step 3b.

### Output format for bare-link analysis

```
## What this thread is about
<2-3 short paragraphs>

## Best current explanation
<short conclusion, clearly separating confirmed facts from hypotheses>

## Supporting checks
<only include if performed>

## Next step
<one suggested action, or offer Databricks/Datadog validation if not yet used>

## Suggested next step
<recommend one of the three follow-up options and list all three>

**Sources:** <all tools/data used>
```

Separate confirmed evidence from hypotheses. Use tables only for structured data that adds clarity. When a specific data table is queried, show a small sample.

## Step 6: Output

Structure the final output as:

```
# Slack Analysis — #<channel_name>

## What this thread is about
<2-3 short paragraphs>

## Best current explanation
<short conclusion>

## Supporting checks
<only if performed>

## <Action Label> (e.g., "Draft Reply", "Summary", "Investigation")

<Action output>

## Suggested Next Step

I recommend: <Option 1/2/3> — <one short reason>

Choose one:
1. **Simple Slack response** — draft a concise reply Ron can paste back into Slack.
2. **Deep check with tools** — targeted follow-up using Jira, other Slack channels, local repos/git, Datadog, and Databricks only when needed.
3. **Heavy Databricks notebook investigation** — create a Databricks notebook with read-only analysis, samples, summary, and notebook link.

---

**Sources:** <list tools/data used: Slack thread, Jira tickets, git commits, etc.>
```

### Reply Drafts

When drafting replies, wrap the text inside a fenced code block (triple backticks) so the user can copy-paste directly without formatting artifacts. Do NOT use `>` blockquote syntax — it pollutes the clipboard.

````
### Draft Reply

```
<the reply text, ready to paste into Slack>
```
````

If the reply references Jira tickets or PRs, include links inline.

## Guards

- **Ignore GMinion.** Strip all messages authored by the GMinion bot before any processing. Do not include them in the timeline, participant list, message count, or any analysis. Treat them as if they don't exist.
- **Read-only.** Never post to Slack, modify Jira, or push code. Analysis and drafting only.
- **Privacy.** Don't expose messages from DMs or private channels the user hasn't explicitly shared.
- **Stale thread.** If the last message is >7 days old, note: `"This thread has been inactive for <N> days — context may be stale."`
- **No redundant sections.** Do not output a metadata table, key-examples table, and timeline if they repeat the same content. Prefer one short high-level section plus investigation sections.
- **Simple-English first.** Start high level, then go deep. The first explanation should be understandable without prior knowledge of the project.
- **No unnecessary paths.** Avoid full file/function/notebook/catalog paths unless explicitly requested.
- **Short answer first.** The first useful answer should usually fit into 2-3 short paragraphs before any deep-dive sections.
