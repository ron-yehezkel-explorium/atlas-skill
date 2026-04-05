# Workflow: Team Timeline

Goal: sync ATB Jira state locally, preserve manual planning edits, and render a Mermaid gantt PNG.

## Trigger

Run only when the user explicitly asks for `team timeline`, `timeline`, `gantt`, or capacity / month planning as a timeline request. Do not run during daily brief or generic Jira reads.

## Files

| File | Purpose |
|---|---|
| `team_timeline/` | Pipeline package — all Jira fetch, merge, schedule, render |
| `team_timeline/config.py` | All static config: Jira defaults, roster, topics, capacity (working days, weekends, holidays), output settings |
| `reference/team-timeline-tickets.md` | Canonical editable ticket state (local-only planning state) |
| `output/Team-Timeline-<stamp>/` | Generated artifacts — do not edit |

**Edit `team_timeline/config.py` to change topics, capacity, holidays, on-call rotation, or Jira defaults.**  
**Edit `team-timeline-tickets.md` to reorder, reassign, or adjust estimates.**  
Never write back to Jira.

## Commands

### Preflight (validate + smoke render)

```bash
python3 -m team_timeline preflight \
  --tickets reference/team-timeline-tickets.md \
  --output-root output
```

### Build (full sync + render)

```bash
python3 -m team_timeline build \
  --tickets reference/team-timeline-tickets.md \
  --output-root output
```

Optional window override:

```bash
python3 -m team_timeline build \
  --tickets reference/team-timeline-tickets.md \
  --output-root output \
  --window-start 2026-04-05 \
  --window-end 2026-05-10
```

Run commands from the `atlas-skill` root directory.

## View range

- Default: **30 calendar days** from `--window-start` (or today) — the chart ends at the earlier of that cap or the last scheduled ticket; tasks that extend past the cap are **clipped** in the graph
- `--full-horizon`: show the full schedule to the last ticket (no 30-day cap)
- `--window-start` / `--window-end`: `YYYY-MM-DD`; `--window-end` is the **inclusive** last day of the chart (overrides the cap)
- On-call generation still uses the same 30-day near-term horizon for scheduling logic

## Output

After a successful build, return to the user:

1. The PNG (`team-timeline.png`) and Mermaid source (`team-timeline.mmd`) from the stamped output folder
2. The JSON line printed to stdout (includes `window_start`, `window_end`, sync counts, timings, `non_working_days_in_window`, and `artifacts`)

**Non-working days** (grey columns): edit `CAPACITY` in `team_timeline/config.py` — `weekend_days`, `global_non_working_days`, and `working_days` (see comments above `CAPACITY` in that file). Per-person time off is `per_person_capacity_events` (lane bars, not column shading).

## Guards

- Never write back to Jira
- Never overwrite `estimation`, `topic`, file order, or section placement for existing tickets
- Missing canonical files → abort with exact path
- If only the view range changes, rerun `build` with new `--window-start` / `--window-end`; no Jira sync needed
