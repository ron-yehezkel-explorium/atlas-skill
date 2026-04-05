# Team Timeline Topics

Editable topic-to-color mapping for team timeline bars. Stored under `reference/team-timeline/`.

## Rules

- Existing ticket `topic` in sibling file `team-timeline-tickets.md` wins.
- New tickets use the first matching topic rule below.
- Add new rows freely.
- Use short `topic` ids safe for CSS selectors.
- `capacity` and `on_hold` are reserved workflow topics.

## Topics

| topic | label | color | aliases |
|---|---|---|---|
| contacts | Contacts / Firmo pipeline | #4F74FF | contacts, firmo, contactout, salutary, bettercontact, email, common-room |
| deliveries | Deliveries | #22A06B | delivery, deliveries, refresh, backfill, commonroom |
| tech_debt | Tech debt | #FF9F1C | cleanup, refactor, audit, qa, writer, debt |
| other | Other | #7C6CF2 | |
| capacity | Capacity | #8B8FA3 | on-call, holiday, vacation, ooo |
| on_hold | On Hold | #C44569 | on hold, blocked |

## Assignment Rule

For new tickets only:

1. first matching explicit local topic if already present
2. else first matching alias from this file using labels + title
3. else `other`
