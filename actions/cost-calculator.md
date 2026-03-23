# Workflow: Databricks Workflow Cost Calculator

Goal: calculate the precise total cost of a Databricks workflow run, broken down by Databricks DBU charges, AWS EC2 compute, and AWS EBS storage.

**Performance target: under 2 minutes.**

## Inputs

- **Required:** Databricks workflow `run_id` (numeric)
- **Optional:** Date override (for billing queries). Defaults to run date.

## Defaults

Use defaults from your system prompt unless user overrides.

- Databricks warehouse ID: `2dfc33368ea84f86`
- EC2 pricing reference: `reference/ec2-pricing.md`

## Step 0: Load Prerequisites

1. Load `databricks-sql` skill for SQL warehouse access.
2. Read `reference/ec2-pricing.md` for EC2 on-demand and spot price lookups.
3. Ensure SQL warehouse is running (`databricks warehouses get <warehouse_id> --output json | jq -r '.state'`). Start if stopped.

## Step 1: Fetch Run Metadata

```bash
databricks jobs get-run <run_id> --output json
```

Extract:
- `run_name`, `job_id`, `start_time`, `end_time`, `run_duration`, `state`
- `job_clusters[]` — fleet type configs, `aws_attributes` (spot policy, `first_on_demand`), `autoscale`
- `tasks[]` — each task's `task_key`, `cluster_instance.cluster_id`, `execution_duration`, `setup_duration`, `run_job_task` (sub-job references)

Key derivations:
- **Run date** (for billing queries): `usage_date` from `start_time` (UTC)
- **Wall-clock duration:** `(end_time - start_time) / 1000` seconds

## Step 2: Resolve Sub-Jobs (Recursive)

For each task with `run_job_task` (delegated job):
1. Find the matching child run via `databricks jobs list-runs --job-id <sub_job_id> --output json`
2. Match by `start_time` overlap with the parent task's time window
3. Recurse into the child run: extract its `tasks[]`, `job_clusters[]`, `cluster_instance.cluster_id`

**Collect ALL unique cluster IDs** across the parent and all child runs.

## Step 3: Query DBU Usage (Exact — from system tables)

Load `databricks-sql` skill. Use warehouse from defaults.

```sql
SELECT
  usage_metadata.cluster_id,
  usage_metadata.node_type,
  sku_name,
  usage_quantity,
  usage_start_time,
  usage_end_time,
  product_features.is_photon,
  product_features.jobs_tier
FROM system.billing.usage
WHERE usage_metadata.cluster_id IN ('<cluster_id_1>', '<cluster_id_2>', ...)
  AND usage_date = '<run_date>'
ORDER BY usage_metadata.cluster_id, usage_start_time
```

This returns the **actual DBU consumption** per cluster, per resolved EC2 instance type, per hour bucket.

## Step 4: Query DBU List Prices

```sql
SELECT sku_name, pricing.default as price_per_dbu
FROM system.billing.list_prices
WHERE cloud = 'AWS'
  AND price_end_time IS NULL
  AND sku_name IN ('<sku_1>', '<sku_2>', ...)
```

Match each usage record's `sku_name` to its list price.

**DBU cost per record** = `usage_quantity * price_per_dbu`

## Step 5: Get Cluster Scaling Events

For each cluster ID:

```bash
databricks clusters events <cluster_id> --output json
```

Extract `CREATING`, `RUNNING`, `UPSIZE_COMPLETED`, `DOWNSIZE_COMPLETED`, `TERMINATING` events.

Derive:
- **Cluster lifetime:** `CREATING` → `TERMINATING` timestamps
- **Node count over time:** track `current_num_workers` from scaling events
- **Driver vs worker count:** always 1 driver + N workers

## Step 6: Calculate EC2 Compute Cost

For each cluster, using data from Steps 1-3 and 5:

### 6a: Identify Spot vs On-Demand

From `job_clusters[].new_cluster.aws_attributes`:
- `first_on_demand=1` → **driver = on-demand**, workers = spot
- `availability=SPOT_WITH_FALLBACK` → workers attempt spot, fallback on-demand

### 6b: Map Instance Types to Prices

The billing table (Step 3) reveals the **actual resolved EC2 instance type** (e.g., `r6i.2xlarge` not the fleet type `r-fleet.2xlarge`).

Look up on-demand and spot prices from `reference/ec2-pricing.md`.

### 6c: Compute Per-Cluster EC2 Cost

```
driver_cost = cluster_lifetime_hours × on_demand_price(driver_instance_type)
worker_cost = Σ (worker_hours × spot_price(worker_instance_type) × worker_count)
cluster_ec2_cost = driver_cost + worker_cost
```

**Heuristic for driver vs worker assignment:**
- The billing table may show multiple instance types per cluster (fleet resolution)
- The instance type with higher total DBU is usually the driver (it runs for the full duration)
- Alternatively, if there's exactly 1 node of one type → that's likely the driver

### 6d: Serverless Nodes (db.* types)

If `usage_metadata.node_type` starts with `db.` → **serverless**. EC2 cost is bundled in DBU price. Do NOT add separate EC2 cost for these.

## Step 7: Calculate EBS Storage Cost

For each cluster:
- Volume config from `job_clusters[].new_cluster.aws_attributes`:
  - `ebs_volume_count` (default: 1)
  - `ebs_volume_size` (default: 100 GB)
  - `ebs_volume_type` (typically `GENERAL_PURPOSE_SSD` = gp3)
- Node count: 1 driver + workers (from Step 5)
- Duration: cluster lifetime in hours

```
ebs_cost = node_count × volume_count × volume_size_gb × hours × gp3_rate_per_gb_hour
```

Where `gp3_rate_per_gb_hour = $0.08 / 730 = $0.000110/GB/hour`

## Step 8: Output

### Structure

```
# Workflow Cost Report — <run_name>
---
## Summary
---
## Cluster Details
---
## DBU Breakdown
---
## EC2 Breakdown
---
## Cost Confidence
```

### Section 1: Summary

```
**Run:** <run_name> (run_id: <run_id>)
**Job ID:** <job_id>
**Status:** <result_state>
**Duration:** <wall_clock_duration>
**Date:** <run_date>
**Total Tasks:** <N> (across <M> clusters)

| Cost Category | Amount |
|---------------|--------|
| Databricks DBU | $X.XXXX |
| AWS EC2 Compute | $X.XXXX |
| AWS EBS Storage | $X.XXXX |
| **Total** | **$X.XXXX** |
```

### Section 2: Cluster Details

One subsection per cluster:

```
### Cluster: <cluster_name or cluster_key>
**Cluster ID:** <cluster_id>
**Lifetime:** <start> → <end> (<hours>h)
**Driver:** <instance_type> (on-demand)
**Workers:** <count> × <instance_type> (spot)
**Autoscale:** <min>-<max> workers
**Photon:** yes/no
**Tasks:** <task_key_1>, <task_key_2>, ...
```

### Section 3: DBU Breakdown

```
| Cluster | Instance Type | SKU | DBUs | $/DBU | Cost |
|---------|---------------|-----|------|-------|------|
| ... | ... | ... | X.XX | $0.15 | $X.XX |
| **Total** | | | **X.XX** | | **$X.XX** |
```

### Section 4: EC2 Breakdown

```
| Cluster | Role | Instance Type | Hours | $/hr | Cost |
|---------|------|---------------|-------|------|------|
| ... | driver | r6i.2xlarge | 1.16 | $0.504 | $0.58 |
| ... | worker (spot) | r5n.2xlarge | 1.16 | $0.18 | $0.21 |
| **Total** | | | | | **$X.XX** |
```

Include EBS as a separate row:
```
| EBS Storage | all | gp3 | <total_node_hours> | $0.011/100GB/hr | $X.XX |
```

### Section 5: Cost Confidence

Rate each component:

| Component | Confidence | Source |
|-----------|------------|--------|
| DBU quantity | **Exact** | `system.billing.usage` |
| DBU price | **Exact** | `system.billing.list_prices` |
| EC2 (on-demand nodes) | **High** | AWS published pricing |
| EC2 (spot nodes) | **Estimated** | ~70% discount heuristic |
| EBS | **High** | AWS published pricing |

Add notes:
- "Spot prices are estimated at 70% discount from on-demand. Actual prices vary by AZ and time."
- "DBU data is sourced directly from Databricks billing system tables."
- If any serverless nodes: "Serverless (db.*) costs are fully captured in DBU — no separate EC2 charge."

### Run Metadata

```
---
**Run metadata:** generated_at=<ISO8601>, run_id=<run_id>, clusters_analyzed=<N>, dbu_records=<N>, ec2_pricing_source=reference/ec2-pricing.md
```

## Edge Cases

### Multi-day runs
Query `system.billing.usage` for all relevant `usage_date` values (from run start date to end date).

### Failed runs
Still calculate cost — clusters were running and DBU was consumed even if tasks failed.

### Serverless jobs (no cluster_id)
If a task has no `cluster_instance` and no `run_job_task`, it may be serverless. Check `system.billing.usage` for the job_id directly:
```sql
SELECT * FROM system.billing.usage
WHERE usage_metadata.job_id = '<job_id>'
  AND usage_date = '<run_date>'
```

### Shared clusters (existing_cluster_id)
If tasks use an existing shared cluster, the cost attribution is partial. Note: "This task ran on shared cluster <id> — cost shown is the proportional DBU consumed during the task window, but EC2 cost is shared."

### Unknown instance types
If an EC2 instance type from billing is not in `reference/ec2-pricing.md`, use the AWS pricing formula:
- Look up a comparable instance from the same family and scale by vCPU/memory ratio
- Flag as **Estimated** in the confidence table
- Suggest updating `reference/ec2-pricing.md`

## Accuracy Notes

The most accurate component is **always the DBU cost** — it comes directly from Databricks system tables with exact quantities and prices.

EC2 cost accuracy depends on:
1. **On-demand nodes:** Very accurate (published AWS prices, stable)
2. **Spot nodes:** Estimated (~70% discount). For exact spot pricing, check AWS Cost Explorer or the Databricks `system.billing.usage` `custom_tags` for spot metadata
3. **EBS:** Accurate but negligible for short-lived job clusters

For production-grade cost tracking, consider querying AWS Cost Explorer API with cluster tags for exact EC2 billing.
