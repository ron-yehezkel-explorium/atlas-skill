---
name: atlas-skill
description: ATB engineering manager copilot using Slack, Jira, Databricks, Git for team status, ownership, execution, and follow-up.
---

# Atlas Team OS

Use markdown knowledge files bundled in this skill directory as the source of truth.

## File Loading

1. **Always read first:** `README.md` (roster + defaults). Abort if unreadable.
2. **Workflow files** — identify intent, load exactly one:
   - Daily brief: `workflows/daily-brief.md`
   - On-call brief: `workflows/on-call-brief.md`
   - Ticket creation: `workflows/tasks-creator.md` (mandatory for any create/open/write Jira request — load before drafting or running `acli jira workitem create`)
   - Slack analysis: `workflows/slack-analyze.md` (when user pastes a Slack link or asks to analyze/respond to a Slack discussion)
3. No known workflow? Answer from README.md + tools only.
4. User-requested format overrides take precedence.

## Tool Routing

- **Local repos first.** When a query mentions a project or repo name (e.g., "enrichments", "mulan", "gaudi"), resolve it against the local repos list in `README.md`. Check `git log` / `git diff` on the matching repo **before** searching Slack or Jira. This applies to questions like "any new X?", "what changed in X?", "updates on X repo?".
- Slack MCP tools (`slack_*`) for Slack data — only after local repo and Jira signals are exhausted or when the question is explicitly about Slack conversations.
- `acli` for Jira (prefer `--json`).
- Local `git log` for repository signals.
- Execute workflow steps directly — no helper scripts.

## Performance

- **Jira first, Slack lazy.** Complete all Jira queries/enrichment before invoking Slack. Only touch Slack when the workflow explicitly requires it (e.g., deep dive).
- **Local repos before Slack.** For project/code questions, check `git log --oneline --since="<window>" <repo_path>` first. Slack is a fallback, not the primary signal for code activity.
- **Parallel enrichment is mandatory.** Batch all `view` calls together, then all `comment list` calls.

## Guards

- **Roster:** Must come from `README.md`. Unreadable = abort. Never invent or cache members.
- **Date window:** Default to today (start-of-day to now). Window doesn't include today = warn: "⚠️ Time window does not cover today — verify intent."
- **No silent fallbacks:** Missing file = abort with exact path (relative to skill directory). Never glob for alternatives.

## Error Handling

MCP `-32601` on capability probes (`prompts/list`, etc.) is expected — note once, move on. MCP init failures must not block Jira workflows.

## Output

- Skill directory files are canonical behavior and context.
- Cite exact commands/tool calls used.
- Logs: key counters (fetched, enriched, errors) and timings only.
