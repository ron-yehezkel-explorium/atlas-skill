# Workflow: Cost Brief

Goal: produce a weekly Databricks cost report for the Atlas team — every process that consumed DBUs, with dates, per-person attribution, interactive-usage summaries, and a full cost breakdown.

**Performance target: under 3 minutes.**

## Inputs

- **Optional:** Time window override. Default: current ISO week (Monday 00:00 UTC → now).
- **Optional:** Team filter override. Default: Atlas roster from `README.md`.

## Defaults

Read defaults from `README.md` unless user overrides.

- Databricks warehouse ID: `2dfc33368ea84f86`
- EC2 pricing reference: `reference/ec2-pricing.md`
- Cost calculation reference: `workflows/workflow-cost.md` (for single-run deep dives)
- Roster emails: all `email` values from the roster table in `README.md`

## Step 0: Load Prerequisites

1. Load `databricks-sql` skill for SQL warehouse access.
2. Read `reference/ec2-pricing.md` for EC2 price lookups.
3. Read roster from `README.md` — extract all team emails into `<roster_emails>`.
4. Ensure SQL warehouse is running. Start if stopped.

## Step 1: Collect All Team Usage (Single Query)

This is the **core query**. It joins billing usage with list prices and attributes every DBU record to a person and workload.

```sql
SELECT
  COALESCE(u.usage_metadata.job_name,
    CASE
      WHEN u.sku_name LIKE '%SQL%' THEN 'SQL Warehouse'
      WHEN u.sku_name LIKE '%ALL_PURPOSE%' THEN 'Interactive Cluster'
      ELSE 'Other'
    END
  ) AS workload_name,
  u.usage_metadata.job_id,
  COALESCE(u.custom_tags['Team'], '-') AS team_tag,
  COALESCE(u.custom_tags['owner'], '-') AS owner_tag,
  COALESCE(u.identity_metadata.run_as, u.identity_metadata.owned_by, '-') AS triggered_by,
  COALESCE(u.custom_tags['project'], '-') AS project,
  u.sku_name,
  MIN(u.usage_start_time) AS first_seen,
  MAX(u.usage_end_time) AS last_seen,
  COUNT(DISTINCT u.usage_metadata.cluster_id) AS clusters,
  COUNT(DISTINCT u.usage_metadata.node_type) AS instance_types,
  SUM(u.usage_quantity) AS total_dbu,
  p.pricing.default AS price_per_dbu,
  ROUND(SUM(u.usage_quantity * p.pricing.default), 4) AS dbu_cost_usd
FROM system.billing.usage u
JOIN system.billing.list_prices p
  ON u.sku_name = p.sku_name
  AND p.cloud = 'AWS'
  AND p.price_end_time IS NULL
WHERE u.usage_date >= '<start_date>'
  AND u.usage_date <= '<end_date>'
  AND (
    u.custom_tags['Team'] IN ('Atlas', 'Padel')
    OR u.custom_tags['owner'] IN ('<@roster_handles>')
    OR u.identity_metadata.run_as IN ('<roster_emails>')
    OR u.identity_metadata.owned_by IN ('<roster_emails>')
  )
GROUP BY 1, 2, 3, 4, 5, 6, 7, 13
ORDER BY dbu_cost_usd DESC
```

### Attribution priority (layered union)

Match if **any** condition is true:

| Priority | Signal | Field | Notes |
|----------|--------|-------|-------|
| 1 | Team tag | `custom_tags['Team']` | Explicit cluster tag: `Atlas`, `Padel` |
| 2 | Owner tag | `custom_tags['owner']` | e.g. `@ron.yehezkel` |
| 3 | Triggerer | `identity_metadata.run_as` | Email of person who launched the run |
| 4 | Resource owner | `identity_metadata.owned_by` | Serverless SQL warehouse owner |

**Include extended team** — people not in roster but on Atlas/Padel-tagged clusters (e.g., `itamar.fradkin`, `shahar.luftig`, `omer.elinav`). List them with a note: `(via Team tag, not in roster)`.

## Step 2: Collect Per-Person Summary

```sql
SELECT
  COALESCE(u.identity_metadata.run_as, u.identity_metadata.owned_by, 'unknown') AS person,
  CASE
    WHEN u.sku_name LIKE '%SQL%' THEN 'SQL Warehouse'
    WHEN u.sku_name LIKE '%ALL_PURPOSE%' THEN 'Interactive Cluster'
    WHEN u.sku_name LIKE '%JOBS%' THEN 'Job Compute'
    ELSE 'Other'
  END AS compute_type,
  SUM(u.usage_quantity) AS total_dbu,
  ROUND(SUM(u.usage_quantity * p.pricing.default), 2) AS dbu_cost_usd
FROM system.billing.usage u
JOIN system.billing.list_prices p
  ON u.sku_name = p.sku_name AND p.cloud = 'AWS' AND p.price_end_time IS NULL
WHERE u.usage_date >= '<start_date>' AND u.usage_date <= '<end_date>'
  AND ( <same attribution filter as Step 1> )
GROUP BY 1, 2
ORDER BY dbu_cost_usd DESC
```

## Step 3: Interactive Usage Summaries (Query History)

For each person with **SQL Warehouse** or **Interactive Cluster** cost > $10, query `system.query.history` to understand what they were doing:

```sql
SELECT
  executed_by,
  COUNT(*) AS query_count,
  SUM(total_duration_ms) / 1000 AS total_seconds,
  COLLECT_SET(statement_type) AS statement_types,
  -- Sample up to 5 distinct table references to infer purpose
  SLICE(
    COLLECT_SET(
      REGEXP_EXTRACT(statement_text, '(?:FROM|JOIN|INTO)\\s+([\\w.]+)', 1)
    ), 1, 5
  ) AS tables_accessed
FROM system.query.history
WHERE start_time >= '<start_timestamp>'
  AND start_time <= '<end_timestamp>'
  AND executed_by IN ('<roster_emails_with_high_interactive_cost>')
  AND statement_type NOT IN ('SET', 'USE', 'DESCRIBE')
GROUP BY 1
```

For each person, also sample a few representative queries to generate a one-line purpose summary:

```sql
SELECT
  executed_by,
  LEFT(statement_text, 200) AS query_preview,
  start_time,
  total_duration_ms
FROM system.query.history
WHERE start_time >= '<start_timestamp>'
  AND start_time <= '<end_timestamp>'
  AND executed_by = '<person_email>'
  AND statement_type = 'SELECT'
  AND total_duration_ms > 5000
ORDER BY total_duration_ms DESC
LIMIT 5
```

From the tables accessed and query previews, **synthesize a one-line summary** of what they were doing. Examples:
- "Investigating contacts_united data quality — counts, schema checks, sampling"
- "Revenue base email validation pipeline monitoring and status checks"
- "Ad-hoc partner service logs analysis, cross-referencing with EDS data"

## Step 4: EC2 Cost Estimation (Jobs Only)

For job compute workloads (SKU contains `JOBS`), estimate the EC2 cost as described in `workflows/workflow-cost.md`:

- Serverless jobs (`SERVERLESS` in SKU or `db.*` node types): EC2 is **bundled in DBU**. Add $0 for EC2.
- Classic jobs: estimate EC2 ≈ DBU cost × 0.93 (based on observed ratios from workflow-cost.md analysis: $1.02 EC2 / $1.10 DBU ≈ 0.93x). This is a rough multiplier — flag as estimated.

For interactive clusters (`ALL_PURPOSE`): EC2 is already significant but harder to attribute per-person on shared clusters. Use the same 0.93x ratio as a rough estimate.

For SQL warehouses (`SQL` in SKU): serverless — EC2 is **bundled**. $0 additional.

## Step 5: Output

### Structure

```
# Cost Brief — <week range>
---
## Attention Required
---
## Team Snapshot
---
## Per Person
### <Person> — $<total>
  ...repeated per person...
---
## All Processes
---
## Calculations
---
## Deep Dive
```

### Section 1: Attention Required

Flag any of:
- Person spending > $200/week → `"<Name> consumed $X this week — review interactive usage"`
- Interactive cluster running > 24h continuous → `"<Name> has a long-running cluster — consider auto-termination"`
- Any `[dev ...]` job names → `"Dev jobs running in production billing: <job_name>"`
- Workload cost > $50 and tagged as non-Atlas team → `"Cross-team workload: <name> ($X) — verify attribution"`

Nothing? Write `None.`

### Section 2: Team Snapshot

```
**Period:** <Mon DD> → <Mon DD, YYYY>
**Total DBU Cost:** $X,XXX.XX
**Est. EC2 Cost:** $X,XXX.XX
**Est. Grand Total:** $X,XXX.XX

| Person | SQL Warehouse | Interactive | Jobs | **Total** |
|--------|:---:|:---:|:---:|:---:|
| ... | $X.XX | $X.XX | $X.XX | **$X.XX** |
| **Team Total** | **$X.XX** | **$X.XX** | **$X.XX** | **$X,XXX.XX** |
```

### Section 3: Per Person

One section per person, sorted by total cost descending. Separated by `---`.

```
### <Name> — $<total_cost>

**Compute breakdown:** SQL $X | Interactive $X | Jobs $X

**Interactive usage summary:** <one-line synthesized summary from Step 3>

**Processes:**

N. **<workload_name>** — $X.XX
   <dates active> | <DBU count> DBU @ $<price>/DBU | SKU: <sku_short>
   <project tag if present>

N+1. ...
```

#### Workload line rules

| Field | Format |
|-------|--------|
| **Dates** | `Mon DD` (single day) or `Mon DD – Mon DD` (range), derived from `first_seen` / `last_seen` |
| **Cost** | DBU cost in USD, 2 decimals |
| **DBU** | Total DBUs, 1 decimal |
| **SKU short** | Strip `PREMIUM_` prefix, lowercase remainder. e.g. `jobs_compute`, `serverless_sql` |
| **Project** | Show if `project != '-'`: `Project: <project>` |
| **Interactive summary** | For SQL Warehouse and Interactive Cluster entries, append the one-line usage summary from Step 3 |

For people with > 10 processes, show the top 10 by cost and collapse the rest:
```
<N more small processes totaling $X.XX>
```

### Section 4: All Processes (Master Table)

Full table of every workload, sorted by cost descending:

```
| # | Workload | Person | Dates Active | DBUs | $/DBU | DBU Cost | Est. EC2 | Est. Total | Type |
|---|----------|--------|--------------|------|-------|----------|----------|------------|------|
| 1 | ... | ... | Mon DD-DD | X.X | $0.70 | $537.91 | $0 | $537.91 | SQL WH |
| ... |
| **Total** | | | | **X,XXX** | | **$X,XXX** | **$XXX** | **$X,XXX** | |
```

Type column values: `SQL WH`, `Interactive`, `Job`, `Job (serverless)`, `Shared Svc`

### Section 5: Calculations

Explain how every number was derived. This section is **mandatory**.

```
## Calculations

### Data Sources
- **DBU quantities:** `system.billing.usage` (exact, from Databricks billing)
- **DBU prices:** `system.billing.list_prices` (exact, current list price per SKU)
- **Query history:** `system.query.history` (for interactive usage summaries)
- **EC2 estimates:** `reference/ec2-pricing.md` + 0.93x DBU ratio heuristic

### Price Per DBU by SKU

| SKU | $/DBU | Applies To |
|-----|-------|------------|
| PREMIUM_JOBS_COMPUTE | $0.15 | Classic job clusters |
| PREMIUM_JOBS_COMPUTE_(PHOTON) | $0.15 | Photon job clusters |
| PREMIUM_JOBS_SERVERLESS_COMPUTE_US_EAST_N_VIRGINIA | $0.35 | Serverless jobs |
| PREMIUM_ALL_PURPOSE_COMPUTE | $0.55 | Interactive notebooks |
| PREMIUM_ALL_PURPOSE_SERVERLESS_COMPUTE_US_EAST_N_VIRGINIA | $0.75 | Serverless notebooks |
| PREMIUM_SERVERLESS_SQL_COMPUTE_US_EAST_N_VIRGINIA | $0.70 | SQL warehouses |

### EC2 Cost Estimation Method

- **SQL Warehouses (serverless):** EC2 is bundled into the DBU price. Additional EC2 = **$0**.
- **Serverless Jobs:** EC2 is bundled into the DBU price. Additional EC2 = **$0**.
- **Classic Jobs:** EC2 ≈ DBU cost × 0.93 (empirical ratio from cluster-level analysis). Drivers run on-demand; workers on spot (~70% discount).
- **Interactive Clusters:** EC2 ≈ DBU cost × 0.93 (same heuristic). These clusters often run for hours, making the EC2 cost significant.

### Attribution Method

Team ownership determined by layered union:
1. `custom_tags['Team']` = Atlas or Padel
2. `custom_tags['owner']` matches roster handle
3. `identity_metadata.run_as` matches roster email
4. `identity_metadata.owned_by` matches roster email

If a workload matches multiple people (shared service), it is attributed to the `run_as` identity.

### Confidence

| Component | Level | Notes |
|-----------|-------|-------|
| DBU quantity | **Exact** | From `system.billing.usage` |
| DBU price | **Exact** | From `system.billing.list_prices` |
| EC2 (serverless) | **Exact** | $0 — bundled in DBU |
| EC2 (classic) | **Estimated** | 0.93x heuristic; spot prices vary |
| Interactive summaries | **Best-effort** | From sampled query history |
```

### Section 6: Deep Dive

```
## Deep Dive

Want details on a specific workload? Reply with the number from the table:
> "3" or "1, 5, 12"

For job workloads, I'll run the full cost calculation from `workflows/workflow-cost.md` with exact EC2 breakdown per cluster. For interactive usage, I'll pull the full query history.
```

#### Deep Dive Behavior (when user replies)

1. **Job workload:** Execute `workflows/workflow-cost.md` for the specific `job_id` — find recent runs, pick the one in the time window, produce full cluster/DBU/EC2 breakdown.
2. **Interactive cluster:** Pull full query history for that person in the time window — show all queries, durations, tables accessed.
3. **SQL warehouse:** Pull query history filtered to that person, show top queries by duration.

### Run Metadata

```
---
**Run metadata:** generated_at=<ISO8601>, window=<start> → <end>, roster_source=README.md, workloads_found=<N>, people=<N>, total_dbu=<N>, total_dbu_cost=$<N>, billing_tables=system.billing.usage+list_prices, query_history=system.query.history
```

## Edge Cases

### Non-roster people on team-tagged clusters
Include them in the report with a note: `(not in roster — matched via Team tag)`. This catches contractors, rotators, or cross-team collaborators using Atlas infrastructure.

### Service principals (UUIDs in run_as)
If `identity_metadata.run_as` is a UUID (not an email), label as `Service Principal (<uuid>)`. These are automated jobs — attribute to the `custom_tags['owner']` if present.

### Shared services (Explorium ID Injector, Events Writer)
These may be triggered by Atlas workflows but run under a different `run_as`. The billing records show the service owner, not the caller. Note: "Shared service — cost attributed to service owner, not calling workflow."

### Zero-cost entries
Some billing records may have `usage_quantity = 0` (e.g., setup time). Exclude these from the report.

### Cross-week runs
A job that started before the time window but ended within it will have partial DBU records in the window. Include only the records within the queried `usage_date` range — the billing table handles this correctly.
