# Workflow: Slack Discussion Analyzer

Goal: fetch a Slack thread from a pasted link, read the full discussion, then execute the user's requested action (formulate a response, summarize, investigate, etc.).

## Step 0: Parse the Slack Link

Extract channel ID and message timestamp from the permalink.

**Format:** `https://<workspace>.slack.com/archives/<CHANNEL_ID>/p<TS_NO_DOT>`

The workspace subdomain varies (e.g., `exploriumai`, `goldinai`, etc.) — do not hardcode it.

**Parsing rule:** strip `p` prefix, insert `.` before the last 6 digits → Slack API `ts`.

Example: `https://exploriumai.slack.com/archives/C011J4X9414/p1709472135123456`
→ channel = `C011J4X9414`, ts = `1709472135.123456`

If the link doesn't match the expected format, ask the user to re-paste it.

## Step 1: Fetch the Discussion

Use Slack MCP tools. Run these in parallel:

1. **Thread replies** — `slack_conversations_replies` with the parsed `channel_id` and `thread_ts`. Set `limit` to `90d` to capture the full thread.
2. **Channel name** — Use `slack_conversations_search_messages` with the original Slack permalink URL as the `search_query`. This returns a single message with the `#channel-name` in the `Channel` column — the most reliable method. **Fallback:** if the search returns nothing, try `slack_channels_list` or use the raw channel ID.

If `slack_conversations_replies` returns nothing or only one message, the link may point to a standalone message (no thread). In that case, present what's available and note: `"This is a standalone message, not a threaded discussion."`

### File Attachments

Messages may include file attachments (indicated by `FileCount > 0` in the CSV). Note file counts in the timeline but do not attempt to download them — flag them for manual review if they seem relevant to the discussion.

## Step 2: Resolve Participants

Cross-reference Slack user IDs from the messages against the team roster in the atlas-skill `README.md` (`skill/atlas-skill/README.md`). For known team members, use their name and role.

For unknown users who appear as **message authors** in the thread CSV, resolve via `slack_users_search` using the display name or username from the CSV. Batch all unknown user lookups in parallel.

For user IDs that only appear in **@mentions** (not as message authors), the CSV doesn't provide a display name. `slack_users_search` cannot look up raw Slack user IDs directly. Flag these as `(unresolved)` in the digest rather than making failing lookups.

Display format: `**Name** (role if known)` for team members, `**Display Name**` for external/unknown, `U0XXXXXXXX (unresolved)` for mention-only IDs that couldn't be resolved.

## Step 3: Build Discussion Digest

Produce a structured digest before executing the user's action:

```
## Discussion Digest

**Channel:** #<channel_name> (or channel ID if name unavailable)
**Started:** <date, time> by **<author>**
**Participants:** <list>
**Thread length:** <N> messages
**Attachments:** <total file count across all messages, or "None">
**Link:** <original permalink>

---

### Timeline

1. **<author>** (<relative time>): <message summary> [N files attached]
2. ...
```

Rules:
- Preserve code blocks, links, and file references from messages.
- Summarize long messages (>5 lines) but keep technical details intact.
- Note file attachments inline with `[N files attached]` when present.
- Flag unresolved questions, action items, and decisions.

## Step 4: Execute the Requested Action

The user will specify what they need. Match intent and execute:

| Intent | Behavior |
|---|---|
| **Formulate a response / reply** | Draft a reply matching Ron's tone (direct, technical, concise). Provide 1-2 variants if the situation is nuanced. Include relevant context from Jira/git if the discussion references tickets or code. |
| **Understand / summarize** | Provide a structured summary: what's being discussed, key positions, unresolved points, and any decisions made. |
| **Investigate / solve** | Identify the technical problem from the thread. Search local repos (`git log`, code), Jira (`acli`), and Databricks if relevant. Propose a solution with evidence. |
| **Draft an update** | Compose a status update or follow-up message based on the thread context and any new information from Jira/git. |
| **Identify action items** | Extract all explicit and implicit action items, assign owners where clear, flag unowned items. |

If the intent is unclear, present the digest (Step 3) and ask: `"What would you like me to do with this discussion?"` with the options above.

## Step 5: Output

Structure the final output as:

```
# Slack Analysis — #<channel_name>

<Discussion Digest from Step 3>

---

## <Action Label> (e.g., "Draft Reply", "Summary", "Investigation")

<Action output>

---

**Sources:** <list tools/data used: Slack thread, Jira tickets, git commits, etc.>
```

### Reply Drafts

When drafting replies, format them in a quoted block so the user can copy-paste directly:

```
### Draft Reply

> <the reply text, ready to paste into Slack>
```

If the reply references Jira tickets or PRs, include links inline.

## Guards

- **Read-only.** Never post to Slack, modify Jira, or push code. Analysis and drafting only.
- **Privacy.** Don't expose messages from DMs or private channels the user hasn't explicitly shared.
- **Stale thread.** If the last message is >7 days old, note: `"This thread has been inactive for <N> days — context may be stale."`
