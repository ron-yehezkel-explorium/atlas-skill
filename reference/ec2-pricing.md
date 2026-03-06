# EC2 On-Demand Pricing Reference (us-east-1)

Last updated: 2026-03-06. Prices in USD/hour.

> These are **on-demand** prices. Spot instances typically cost 60-80% less.
> For spot estimation, apply a 70% discount unless the user provides actual spot data.

## Common Instance Types (Seen in Explorium Databricks)

### Memory-Optimized (R-family) — used for Spark workers/drivers

| Instance | vCPU | Memory (GiB) | On-Demand $/hr | Est. Spot $/hr | Fleet Type |
|----------|------|---------------|----------------|----------------|------------|
| r5.large | 2 | 16 | 0.126 | 0.038 | r-fleet.large |
| r5.xlarge | 4 | 32 | 0.252 | 0.076 | r-fleet.xlarge |
| r5.2xlarge | 8 | 64 | 0.504 | 0.151 | r-fleet.2xlarge |
| r5n.xlarge | 4 | 32 | 0.298 | 0.089 | r-fleet.xlarge |
| r5n.2xlarge | 8 | 64 | 0.596 | 0.179 | r-fleet.2xlarge |
| r5d.xlarge | 4 | 32 | 0.288 | 0.086 | r-fleet.xlarge |
| r5d.2xlarge | 8 | 64 | 0.576 | 0.173 | r-fleet.2xlarge |
| r5dn.xlarge | 4 | 32 | 0.334 | 0.100 | r-fleet.xlarge |
| r5dn.2xlarge | 8 | 64 | 0.668 | 0.200 | r-fleet.2xlarge |
| r6i.xlarge | 4 | 32 | 0.252 | 0.076 | r-fleet.xlarge |
| r6i.2xlarge | 8 | 64 | 0.504 | 0.151 | r-fleet.2xlarge |
| r6id.xlarge | 4 | 32 | 0.286 | 0.086 | r-fleet.xlarge |
| r6id.2xlarge | 8 | 64 | 0.572 | 0.172 | r-fleet.2xlarge |
| r6in.xlarge | 4 | 32 | 0.282 | 0.085 | r-fleet.xlarge |
| r6in.2xlarge | 8 | 64 | 0.564 | 0.169 | r-fleet.2xlarge |
| r6idn.xlarge | 4 | 32 | 0.318 | 0.095 | r-fleet.xlarge |
| r6idn.2xlarge | 8 | 64 | 0.636 | 0.191 | r-fleet.2xlarge |
| r4.xlarge | 4 | 30.5 | 0.266 | 0.080 | legacy |
| r6gd.2xlarge | 8 | 64 | 0.460 | 0.138 | rgd-fleet.2xlarge |
| r6gd.4xlarge | 16 | 128 | 0.921 | 0.276 | rgd-fleet.4xlarge |
| r7gd.2xlarge | 8 | 64 | 0.484 | 0.145 | rgd-fleet.2xlarge |
| r7gd.4xlarge | 16 | 128 | 0.968 | 0.290 | rgd-fleet.4xlarge |

### Compute-Optimized (C-family) — used for CPU-heavy tasks

| Instance | vCPU | Memory (GiB) | On-Demand $/hr | Est. Spot $/hr | Fleet Type |
|----------|------|---------------|----------------|----------------|------------|
| c5.xlarge | 4 | 8 | 0.170 | 0.051 | c-fleet.xlarge |
| c5.2xlarge | 8 | 16 | 0.340 | 0.102 | c-fleet.2xlarge |
| c5n.xlarge | 4 | 10.5 | 0.216 | 0.065 | c-fleet.xlarge |
| c6i.xlarge | 4 | 8 | 0.170 | 0.051 | c-fleet.xlarge |
| c6in.xlarge | 4 | 8 | 0.189 | 0.057 | c-fleet.xlarge |

### General Purpose (M-family)

| Instance | vCPU | Memory (GiB) | On-Demand $/hr | Est. Spot $/hr | Fleet Type |
|----------|------|---------------|----------------|----------------|------------|
| m5.large | 2 | 8 | 0.096 | 0.029 | m-fleet.large |
| m5.xlarge | 4 | 16 | 0.192 | 0.058 | m-fleet.xlarge |
| m5.2xlarge | 8 | 32 | 0.384 | 0.115 | m-fleet.2xlarge |
| m5d.2xlarge | 8 | 32 | 0.452 | 0.136 | m-fleet.2xlarge |
| m5n.xlarge | 4 | 16 | 0.238 | 0.071 | m-fleet.xlarge |
| m5n.2xlarge | 8 | 32 | 0.476 | 0.143 | m-fleet.2xlarge |
| m6i.xlarge | 4 | 16 | 0.192 | 0.058 | m-fleet.xlarge |
| m6i.2xlarge | 8 | 32 | 0.384 | 0.115 | m-fleet.2xlarge |
| m6g.large | 2 | 8 | 0.077 | 0.023 | m-fleet.large (graviton) |
| m6g.xlarge | 4 | 16 | 0.154 | 0.046 | m-fleet.xlarge (graviton) |
| m6gd.2xlarge | 8 | 32 | 0.362 | 0.109 | m-fleet.2xlarge (graviton) |
| m6gd.4xlarge | 16 | 64 | 0.724 | 0.217 | m-fleet.4xlarge (graviton) |
| m6id.2xlarge | 8 | 32 | 0.434 | 0.130 | m-fleet.2xlarge |
| m6in.xlarge | 4 | 16 | 0.213 | 0.064 | m-fleet.xlarge |
| m6in.2xlarge | 8 | 32 | 0.426 | 0.128 | m-fleet.2xlarge |
| m7g.xlarge | 4 | 16 | 0.163 | 0.049 | m-fleet.xlarge (graviton) |

### GPU Instances (G-family)

| Instance | vCPU | Memory (GiB) | GPU | On-Demand $/hr | Est. Spot $/hr | Fleet Type |
|----------|------|---------------|-----|----------------|----------------|------------|
| g6.xlarge | 4 | 16 | 1x L4 | 0.805 | 0.242 | g-fleet.xlarge |

### Storage-Optimized (I-family)

| Instance | vCPU | Memory (GiB) | On-Demand $/hr | Est. Spot $/hr | Fleet Type |
|----------|------|---------------|----------------|----------------|------------|
| i3.xlarge | 4 | 30.5 | 0.312 | 0.094 | i-fleet.xlarge |
| i3.2xlarge | 8 | 61 | 0.624 | 0.187 | i-fleet.2xlarge |

## Databricks Serverless (db.* types)

These are Databricks-managed serverless instances. EC2 cost is **bundled into the DBU price** — there is no separate EC2 charge.

| Node Type | DBU/hr (approx) | Notes |
|-----------|-----------------|-------|
| db.xxsmall | variable | Serverless SQL |
| db.xsmall | variable | Serverless SQL |
| db.small | variable | Serverless SQL |
| db.large | variable | Serverless SQL |
| db.xlarge | variable | Serverless SQL |

For serverless, the DBU cost from `system.billing.usage` is the **total cost** — no EC2 to add.

## EBS Storage

| Volume Type | $/GB/month | $/GB/hour |
|-------------|-----------|-----------|
| gp3 (default) | 0.08 | 0.000110 |
| gp2 | 0.10 | 0.000137 |

Formula: `nodes * volume_size_gb * hours * $/GB/hour`

## Spot Pricing Notes

- Databricks fleet types (e.g., `r-fleet.2xlarge`) resolve to actual EC2 instances at runtime
- `first_on_demand=1` in `aws_attributes` means: **driver = on-demand, workers = spot**
- `SPOT_WITH_FALLBACK` means workers try spot, fall back to on-demand if unavailable
- Actual spot prices fluctuate — use 70% discount as default estimate
- The billing table (`system.billing.usage`) shows the **actual resolved instance type** — always prefer this over the fleet type
