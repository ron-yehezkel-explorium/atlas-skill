# Action: Self-Improver

Goal: analyze the current session for suboptimal agent behavior patterns, extract generic lessons, and apply durable improvements to atlas-skill files so future sessions run the optimal path from the start.

## Trigger

- User says "self-improve", "self-improvement", "learn from this", or similar meta-feedback about agent behavior in the current session.
- User observes the agent taking a non-optimal path first, then correcting itself, and wants to prevent the detour in future sessions.

## Write Scope

**All files inside the atlas-skill directory are writable:**
- `SKILL.md` — core routing, performance rules, guards, learned rules
- `actions/*.md` — action workflow files
- `briefs/*.md` — brief workflow files
- `reference/*.md` — reference data files
- `PROMPT.md` — canonical roster, defaults, and routing (loaded into agent system prompt)

**Everything outside the atlas-skill directory is off-limits.** Never modify `AGENTS.md`, other skill folders, or any file outside `~/.config/opencode/skill/atlas-skill/`.

## Where Improvements Land

Match the improvement to the right file:

| Improvement type | Target file |
|-----------------|-------------|
| Tool ordering, parallelism, context-gathering heuristics | `SKILL.md` → appropriate section (Tool Routing, Performance, Guards) or `## Learned Rules` |
| Workflow step sequencing, missing steps, wrong step order | The specific `actions/*.md` or `briefs/*.md` workflow file |
| Missing guard rails, safety checks | `SKILL.md` → Guards section |
| Output formatting rules | `SKILL.md` → Output section |
| General behavioral patterns that don't fit a specific workflow | `SKILL.md` → `## Learned Rules` |

## Principles

1. **Generic only.** Never mention specific ticket IDs, file names, function names, Slack links, or domain details. Extract the *behavioral pattern*, not the instance.
2. **Additive by default.** Append new rules. Only modify existing rules if they directly conflict.
3. **Minimal surface.** Each improvement should be one concise rule or guideline — no essays.
4. **Idempotent.** If the lesson already exists anywhere in atlas-skill files, skip it. Never duplicate.
5. **Scoped to agent behavior.** Only improve tool usage, ordering, parallelism, skill loading, context gathering, output formatting, and decision-making heuristics. Never change domain knowledge, team roster, or business logic.
6. **Preserve voice.** Match the existing tone and structure of the target file (direct, terse, imperative).

## Step 1: Session Replay Analysis

Scan the current conversation history and identify instances where:

- The agent took a wrong approach first, then corrected itself
- The agent made unnecessary tool calls (redundant fetches, serial calls that could be parallel)
- The agent loaded the wrong skill or forgot to load a skill
- The agent asked a clarifying question it could have inferred
- The agent produced output in a suboptimal format then reformatted
- The agent used the wrong tool for the job (e.g., Bash grep instead of Grep tool)
- The agent missed context it should have gathered upfront
- The agent made multiple rounds to accomplish what could be done in one
- The agent modified a file it should not have touched
- A workflow file had missing or ambiguous steps that caused the agent to improvise badly

For each instance, extract:

| Field | Description |
|-------|-------------|
| **What happened** | Brief factual description of the suboptimal behavior |
| **Why it's suboptimal** | Time wasted, tokens burned, user had to intervene |
| **Optimal path** | What the agent should have done from the start |
| **Generic rule** | A tool/workflow directive that prevents this class of mistake |
| **Target file** | Which atlas-skill file should receive this rule |

## Step 2: Deduplicate Against Existing Content

Read all atlas-skill files that are targets for the proposed rules. For each candidate rule:

1. Check if an existing rule already covers this behavior (even partially)
2. If covered → skip, note "already addressed by: <existing rule snippet>"
3. If partially covered → propose a refinement (tighten, not replace)
4. If net new → mark for insertion with target file and section

## Step 3: Draft Improvements

For each non-duplicate rule, draft the exact text to insert.

**Each rule must be:**
- Imperative voice ("Always X before Y", "Never Z without W")
- Tool-generic where possible (refer to tool categories, not specific tool names when the pattern applies broadly)
- Testable — another agent reading this rule should know unambiguously whether it's following it

For `SKILL.md` Learned Rules, prefix with a category tag: `[tool-order]`, `[parallelism]`, `[context-gathering]`, `[file-safety]`, `[output]`, `[skill-loading]`, `[decision]`

For workflow files, integrate naturally into the existing step structure.

## Step 4: Present for Approval

Show the user:

```
## Self-Improvement Report

### Patterns Detected
1. <pattern summary> → <generic rule> → <target file>
2. ...

### Proposed Changes

**File: <target_file>**
**Section: <section_name>**
+ <new rule text>

**File: <target_file>**
**Section: <section_name>**
~ <modified rule text> (was: <old text>)

### Skipped (already covered)
- <pattern> → covered by: "<existing rule>" in <file>
```

**Wait for user approval before applying any changes.**

## Step 5: Apply Changes

After user confirms:

1. Read current version of each target file
2. Apply approved insertions/modifications
3. Re-read each modified file to verify correctness
4. Show a brief summary of what changed in each file

## Guards

- **Never auto-apply.** Always present changes and wait for explicit user approval.
- **Stay inside atlas-skill/.** Never modify any file outside the atlas-skill directory. This is the hard boundary.
- **Never add use-case-specific rules.** If a rule can only be understood with context from the current session's specific task, it's too specific — generalize further or discard.
- **Never remove existing rules.** Only add or refine. If an existing rule seems wrong, flag it for the user but don't delete.
- **Max 5 rules per session.** If more than 5 patterns are found, prioritize by impact (time/tokens saved) and present the top 5. Offer to add more in a follow-up.
- **Confidence rating:** High (clear pattern, obvious fix), Medium (pattern exists but rule phrasing may need tuning), Low (edge case, may not generalize). Only auto-suggest High/Medium. Present Low as "optional consideration."
