# Atlas Management Knowledge Base

Use this directory as the single source of operational knowledge for Atlas mode.

## Team Roster

Source of truth for person resolution.

| key | name | email | slack_user_id | slack_handle | role |
|---|---|---|---|---|---|
| ron | Ron Yehezkel | ron.yehezkel@explorium.ai | U088JLP938B | @ron.yehezkel | |
| yaara | Yaara Yona | yaara.yona@explorium.ai | U084J2LG5S9 | @yaara.yona | |
| rani | Rani Khoury | rani.khoury@explorium.ai | U05KP3JLSDR | @rani.khoury | |
| itai | Itai Dagan | itai.dagan@explorium.ai | U01N01N9U7N | @itai.dagan | |
| danielle | Danielle Gan | danielle.gan@explorium.ai | U09UZCYQU04 | @danielle.gan | |

### Resolution Rules

- Match person input against `key`, `name`, `email`, `slack_user_id`, or `slack_handle`.
- Use case-insensitive matching.
- If more than one person matches, stop and ask for exact `key`.

## Runtime Defaults

- Jira project: `ATB`
- Jira board id: `154`
- Databricks warehouse id: `2dfc33368ea84f86`
- Local repos for team brief:
  - `/Users/ron.yehezkel/CursorProjects/tube-projects`
  - `/Users/ron.yehezkel/CursorProjects/enrichments`
  - `/Users/ron.yehezkel/CursorProjects/mulan`
  - `/Users/ron.yehezkel/CursorProjects/atlas-jobs`
  - `/Users/ron.yehezkel/CursorProjects/explorium-data-model`
  - `/Users/ron.yehezkel/CursorProjects/gaudi`
  - `/Users/ron.yehezkel/CursorProjects/emlite`

## Workflows

- `workflows/daily-brief.md`: team-wide daily brief playbook.
- `workflows/on-call-brief.md`: on-call brief playbook (atlas-oncall channels, Jira, Databricks).
- `workflows/slack-analyze.md`: Slack discussion analyzer — fetch a thread from a pasted link, digest it, then formulate replies, investigate, summarize, or extract action items.
- `workflows/workflow-cost.md`: Databricks workflow cost calculator — compute exact DBU, EC2, and EBS costs for a given run ID.
- `workflows/cost-brief.md`: Weekly team cost brief — all Atlas team Databricks processes, per-person breakdown, interactive usage summaries, full cost calculations.
- `reference/ec2-pricing.md`: EC2 on-demand and spot pricing reference for common instance types.
