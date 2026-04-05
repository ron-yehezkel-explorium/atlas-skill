# Workflow: Team Timeline

Goal: sync local timeline state from ATB Jira, preserve manual planning edits, and generate a single Mermaid gantt PNG for a requested view range.

## Trigger

Run only when the user explicitly asks for:
- `team timeline`
- `timeline`
- `gantt`
- capacity planning / month planning phrased as a timeline request

Do not run during daily brief or generic Jira reads.

## Defaults

Use defaults from the system prompt unless the user overrides.

- Jira project: `ATB`
- Jira board: `154`
- Timezone: `Asia/Jerusalem`
- Default view range: today → today + 30 calendar days
- Output renderer: Mermaid CLI via `npx -y @mermaid-js/mermaid-cli`

## Canonical Files

Read all three before doing anything else from the dedicated directory:

- `reference/team-timeline/team-timeline-tickets.md`
- `reference/team-timeline/team-timeline-capacity.md`
- `reference/team-timeline/team-timeline-topics.md`

These are the source of truth. Output folders are generated artifacts only.

## Step 0: Resolve View Range

Support:

- `team timeline` → default 30 days from today
- `team timeline 14d`
- `team timeline next 6 weeks`
- `team timeline 2026-04-05 to 2026-05-10`

Rules:

1. Always sync **all** tracked tickets first.
2. The view range only limits what is rendered, not what is synced or scheduled.
3. Start scheduling from **today**, even if the rendered window starts later.

## Step 1: Jira Sync Inputs

Use Atlassian MCP Jira tools. Run the three status searches in parallel.

### Query 1: In Progress

```text
project = ATB AND status = "In Progress" ORDER BY Rank ASC
```

### Query 2: To Do

```text
project = ATB AND status = "To Do" ORDER BY Rank ASC
```

### Query 3: On Hold

```text
project = ATB AND status = "On Hold" ORDER BY Rank ASC
```

Fields:

```text
issuekey,summary,status,assignee,labels,parent,subtasks,issuetype,updated
```

Paginate until all results are fetched.

## Step 2: Normalize Jira Tickets

For every fetched issue:

1. Keep only roster assignees plus unassigned.
2. Ignore non-roster assignees completely.
3. Map empty assignee and `Former user` to `unassigned`.
4. Keep subtasks.
5. Keep issues with no subtasks.
6. Drop parent issues that have subtasks. Timeline shows leaf work only.

Status buckets:

- `In Progress`
- `To Do`
- `On Hold`

## Step 3: Merge Into `reference/team-timeline/team-timeline-tickets.md`

### Local authority rules

For **existing tickets**, preserve:

- file order
- section placement
- `assignee`
- `topic`
- `estimation`

For **existing tickets**, sync only:

- `title`
- `status`
- `parent_epic`
- `labels`
- `last_synced`

For **new tickets**:

1. Insert into the matching status bucket.
2. Insert into the Jira assignee section (`unassigned` if no assignee / former user).
3. Place it using Jira rank relative to nearby Jira tickets already present in that same bucket.
   - first: after the closest preceding Jira neighbor already present
   - else: before the closest following Jira neighbor already present
   - else: append to the end of that section
4. Set default fields:
   - `assignee` = section key
   - `topic` = first matching topic from `reference/team-timeline/team-timeline-topics.md`, else `other`
   - `estimation` = `1`
   - `last_synced` = current local timestamp

For **removed tickets**:

- delete them from the canonical ticket file if they are no longer in `In Progress`, `To Do`, or `On Hold`

### Section semantics

- Ticket order inside a section is the local simulation order.
- Moving a ticket between person sections simulates reassignment.
- Moving a ticket within a section simulates priority changes.
- `assignee` must match the section name after sync.

## Step 4: Read Capacity / Calendar Rules

Read `reference/team-timeline/team-timeline-capacity.md` and apply all of these:

### Working calendar

- Working days: Sunday–Thursday
- Weekend days: Friday, Saturday
- Mermaid must mark Fri/Sat as excluded weekend days

### Global non-working days

Apply all explicit global days/blocks from the file. Never overwrite them during sync.

### Per-person capacity events

Apply all explicit person events from the file. Never overwrite them during sync.

### On-call rotation

Use the local rotation metadata in the file:

- rotation order
- current on-call owner
- changeover: Tuesday 12:00 local time
- representation: one full-day capacity event labeled `On-call`

Generate weekly on-call events for the scheduled horizon using that rotation order. The local file is the authority.

## Step 5: Build the Schedule

### Main developer flow

For each developer lane, schedule in this exact order:

1. all `In Progress` tickets in local file order
2. then all `To Do` tickets in local file order

Include these lanes:

- `ron`
- `yaara`
- `rani`
- `itai`
- `danielle`
- `unassigned`

Rules:

1. Start from today.
2. No overlap.
3. Whole days only.
4. Due dates do **not** reorder work.
5. Capacity events block the lane exactly like tasks.
6. A ticket may continue after a weekend or holiday, but its rendered bar must never cross that gap as one continuous block.

### On Hold flow

Render `On Hold` in a separate shared section.

Rules:

- preserve local order
- do not mix into developer lanes
- do not consume developer capacity

## Step 6: Split Across Non-Working Gaps

Never render a task or capacity event as a single bar across:

- Friday
- Saturday
- global non-working days
- per-person capacity blocks in the middle of work

Instead:

1. split into contiguous working-day chunks
2. label chunks with suffixes only when split is needed:
   - `Backfill 1/2`
   - `Backfill 2/2`
3. keep chunks contiguous in working time
4. blank space between split chunks is allowed only for:
   - weekends
   - explicit global non-working days
   - explicit per-person capacity events

Never create arbitrary idle gaps.

## Step 7: Labels and Truncation

### Base label

Use title only. Do **not** render Jira keys in task bars.

### Parent / epic

Store parent/epic in the canonical file, but do not prepend it to gantt bar labels by default. Keep labels short.

### Fitting rule

Cut labels only when required.

Process:

1. Start with the full base label.
2. If a task is split, append `n/m`.
3. Render a temporary SVG with Mermaid CLI.
4. Inspect the SVG.
5. If a task text is outside the bar (`taskTextOutsideRight` / `taskTextOutsideLeft`), shorten only that task label and re-render.
6. Repeat until all task labels fit inside bars or no further useful shortening remains.

Shortening rules:

- first remove low-value trailing words
- then shorten to a compact stem
- finally add `...`

Do not shorten labels that already fit.

## Step 8: Topics and Colors

Read `reference/team-timeline/team-timeline-topics.md`.

Rules:

1. Existing ticket `topic` in the canonical ticket file wins.
2. New tickets use the first matching topic rule from the topics file.
3. Capacity events always use topic `capacity`.
4. On Hold bars always use topic `on_hold`.

Generate Mermaid CSS selectors by topic id in task ids. Example pattern:

```text
rect[id*="contacts_"] { fill: <color>; stroke: <stroke>; }
```

The topics file must remain human-editable so new topics can be added later without changing workflow logic.

## Step 9: Render Mermaid

Create a timestamped output folder:

```text
output/Team-Timeline-<YYYYMMDD-HHMMSS>/
```

Write:

- `team-timeline.mmd`
- `team-timeline.png`
- `team-timeline.md`

Use Mermaid CLI:

```text
npx -y @mermaid-js/mermaid-cli -i "<mmd>" -o "<png>" -e png -b white -w 5200 -s 1
```

For label-fit checks, it is allowed to render a temporary SVG in the same output directory and delete it afterwards. Do not keep SVG as a final artifact.

## Step 10: Output

Return:

1. the PNG attachment
2. the Mermaid code block
3. a short metadata block:

```text
window=<start> → <end>
synced_in_progress=<N>
synced_to_do=<N>
synced_on_hold=<N>
new_tickets=<N>
removed_tickets=<N>
auto_estimation_count=<N>
output_dir=<short folder name>
```

## Guards

- Never write anything back to Jira.
- Never overwrite manual `estimation`, `topic`, file order, or section placement for existing tickets.
- Never overwrite capacity or holiday data from the local capacity file.
- Never render Jira keys inside bars.
- Never let a rendered bar cross a weekend/non-working gap as one continuous segment.
- Missing canonical files = abort with exact path.
- If the user asks for a different view range, reuse the same synced ticket state and only change the rendered window.
