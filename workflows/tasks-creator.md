# Tasks Creator: Jira Tasks (ATB)

Use this workflow when creating a new Jira task so ticket content is consistent, readable, and easy to edit in Jira UI.

## Trigger
- Any request to create/open/write a new Jira ticket/task/issue.

## Content Format
- Use plain text only in `--description`.
- Do not send ADF JSON.
- Use fixed sections in this exact order:
  - `Problem Statement`
  - `Goal`
  - `Scope of Work`
  - `Acceptance Criteria`

Template:
```text
Problem Statement

Currently, new technologies added to technographics_data are not immediately searchable. The autocomplete labels and indexes only refresh when the Business Catalog labels/index job runs. This creates a manual dependency, leading to stale autocomplete results and operational overhead.

Goal

Automatically trigger the Business Catalog web-tech labels reindex immediately following every successful Technographics production update.

Scope of Work

- Trigger Mechanism: Integrate a post-success hook in the Technographics production pipeline to initiate the labels indexing flow.
- Target Indexes: Reindex the following specific components:
  - bc_labels_web_tech_stack
  - bc_labels_web_tech_categories
- Observability: Implement failure visibility through automated alerts and structured logging.

Acceptance Criteria

- Automation: Newly added technologies must appear in autocomplete without requiring manual job intervention.
- Reliability: The Label Index job is successfully auto-triggered and completes its lifecycle.
- Traceability: System failures must be visible in [Slack/PagerDuty/Monitoring Tool] with direct, traceable links to the specific run logs.
```

## Create Task (with epic)
```bash
acli jira workitem create   --project "ATB"   --type "Task"   --summary "Action-first short title"   --description "Problem Statement

...

Goal

...

Scope of Work

- Trigger Mechanism: ...
- Target Indexes: ...
  - bc_labels_web_tech_stack
  - bc_labels_web_tech_categories
- Observability: ...

Acceptance Criteria

- Automation: ...
- Reliability: ...
- Traceability: ..."   --parent "ATB-1354"   --assignee "@me"   --json
```

`--parent` is the epic connection in this Jira setup.

## Verify Link + Content
```bash
acli jira workitem view ATB-1234 --fields "summary,parent,description" --json
```
