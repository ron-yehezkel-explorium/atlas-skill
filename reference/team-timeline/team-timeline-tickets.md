# Team Timeline Tickets

Canonical local state for team timeline sync. Stored under `reference/team-timeline/`.

## Rules

- File order is the local schedule order.
- Section placement is the local effective assignee and status bucket.
- Existing tickets keep their local order, `assignee`, `topic`, and `estimation` during sync.
- Sync updates only `title`, `status`, `parent_epic`, `labels`, and `last_synced` for existing tickets.
- New tickets default to `estimation: 1`.
- Edit this file directly to simulate reorder or reassignment.

## In Progress

### ron

### yaara

- key: ATB-711
  title: adjust workforce enrichcment
  assignee: yaara
  topic: other
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1359
  title: Analyze and improve seniority fill rates and classification logic
  assignee: yaara
  topic: other
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1518
  title: oncall || swordfish redeliver April data
  assignee: yaara
  topic: other
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1517
  title: Salutary March 2026 Dataset: Fuse SAL to CO using linkedin_url_entity_urn_url, then URL
  assignee: yaara
  topic: contacts
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

### rani

- key: ATB-546
  title: Create automate Task / Job / Notebook that overwrite in PG and Elastic and then save it to whitelist table
  assignee: rani
  topic: other
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1176
  title: Terraform jobs for projects/data_deliveries/connectbase/connectbase_us
  assignee: rani
  topic: deliveries
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1480
  title: Re-deliver firmographics to Common Room after EDS run (relevancy score fix included)
  assignee: rani
  topic: contacts
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1454
  title: Fix text_to_organization_name UDF (amazoncom bug)
  assignee: rani
  topic: other
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1349
  title: Transition madison logic to DBT & Terraform
  assignee: rani
  topic: other
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1029
  title: Improve company website normalization and accuracy
  assignee: rani
  topic: other
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1076
  title: Fix ticker public flag consistency validation
  assignee: rani
  topic: other
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

### itai

- key: ATB-1252
  title: T9 - Production cutover + archive mulan
  assignee: itai
  topic: other
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1449
  title: Add "Has Profile Picture" column (Y/N/Null) to contacts table and propagate to data delivery & Common Room
  assignee: itai
  topic: contacts
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

### danielle

- key: ATB-1035
  title: Remove headquarter struct column from mart_entities
  assignee: danielle
  topic: other
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1393
  title: Remove Synthetic Placeholder Emails from Contacts Pipeline
  assignee: danielle
  topic: contacts
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

### unassigned

- key: ATB-516
  title: include claimed companies with no location
  assignee: unassigned
  topic: other
  status: In Progress
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

## To Do

### ron

- key: ATB-1501
  title: shutdown atlas jobs delivery notebook
  assignee: ron
  topic: deliveries
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1500
  title: Executive email guessing into Contacts pipeline
  assignee: ron
  topic: contacts
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1494
  title: Retain hashed PDL personal-email matching and remove PDL work/phone data
  assignee: ron
  topic: contacts
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1499
  title: Analyze quarterly Bright Data refresh value for Madison-Logic tech stack delivery
  assignee: ron
  topic: deliveries
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

### yaara

- key: ATB-1387
  title: Revert temporary contacts-run workaround (23-month window + >50 connections)
  assignee: yaara
  topic: contacts
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1492
  title: Corrupted contact name from Salutary provider - double-encoding of umlauts (e.g. ö → ãâ)
  assignee: yaara
  topic: contacts
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1346
  title: Review EDM Email Validation - Valid Emails Incorrectly Flagged as Invalid
  assignee: yaara
  topic: contacts
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1431
  title: Split tests from ES write notebook
  assignee: yaara
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1042
  title: Extract LinkedIn URLs from Company Websites to Improve Data Coverage
  assignee: yaara
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1475
  title: Implement COPY job for data delivery
  assignee: yaara
  topic: deliveries
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1476
  title: Migrate customers to COPY-based delivery mechanism
  assignee: yaara
  topic: deliveries
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1477
  title: Build validation job for delivery outputs
  assignee: yaara
  topic: deliveries
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

### rani

- key: ATB-1373
  title: Find alternative sources for company URL when URL is not available
  assignee: rani
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1463
  title: Add Better Contacts as a supported contacts provider in the Contacts United pipeline
  assignee: rani
  topic: contacts
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1353
  title: Migrate data deliveries to terraform
  assignee: rani
  topic: deliveries
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1375
  title: Define automatic contacts refresh trigger and contact-based delivery scheduling
  assignee: rani
  topic: contacts
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1398
  title: Automate website changes post-run compression and raw data cleanup
  assignee: rani
  topic: tech_debt
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1403
  title: Standardize event_time_col across all event pipelines
  assignee: rani
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1438
  title: Limit anniversary event processing to director+ to reduce ETL load
  assignee: rani
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1439
  title: Prevent website changes quarterly run from creating excessive S3 storage costs
  assignee: rani
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1440
  title: Automate and schedule website changes process to run quarterly
  assignee: rani
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

### itai

- key: ATB-833
  title: Unity migration for Mulan - Placeholder
  assignee: itai
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1488
  title: Improve location accuracy for stale or mismatched records
  assignee: itai
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1478
  title: Entity linking: name similarity matcher wrongly links "Simple Air" (HVAC) to "Simplilearn" (ed-tech), corrupting google_business_category
  assignee: itai
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

### danielle

- key: ATB-1383
  title: Investigate job title abbreviation synonyms/aliases not returning equivalent results (CEO-Chief Executive Officer, CTO-Chief Technology Officer...)
  assignee: danielle
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1457
  title: Remove Common Room Hashed Email Dedup Workaround After Permanent Pipeline Fix
  assignee: danielle
  topic: contacts
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1464
  title: Implement PG writer improvements plan from March writing conclusions
  assignee: danielle
  topic: tech_debt
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1227
  title: industry classification design for firmographics
  assignee: danielle
  topic: contacts
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1377
  title: Provider data ingestion monitoring: detect and alert when no new data is delivered before running ETL
  assignee: danielle
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1334
  title: Remove Redundant Columns from Silver Table
  assignee: danielle
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1108
  title: Fix missing SIC code descriptions (1,023 codes without descriptions)
  assignee: danielle
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

### unassigned

- key: ATB-526
  title: Check private beta of Databricks
  assignee: unassigned
  topic: other
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-541
  title: Analyze the change between dumps of email validations
  assignee: unassigned
  topic: contacts
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-534
  title: Create automated job that refresh the emails
  assignee: unassigned
  topic: contacts
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-543
  title: what changes need to be made in EDS WRITER and in elastic?
  assignee: unassigned
  topic: tech_debt
  status: To Do
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

## On Hold

### shared

- key: ATB-1432
  title: Generate zb_domain values - email validation provider change
  assignee: rani
  topic: contacts
  status: On Hold
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1453
  title: ContactOut inferred_months_experience only counts current job, not full work history
  assignee: rani
  topic: contacts
  status: On Hold
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1365
  title: Missing 7 millions addresses from Factori
  assignee: rani
  topic: other
  status: On Hold
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1473
  title: Inject BetterContact emails into Contacts United for Happily via whitelist (gap-fill only)
  assignee: rani
  topic: contacts
  status: On Hold
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-517
  title: make companies with no location have country "unknown"
  assignee: unassigned
  topic: other
  status: On Hold
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-986
  title: Add Cash and Cash Equivalents to Firms Financial Indicators enrichment
  assignee: unassigned
  topic: other
  status: On Hold
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1399
  title: Remove backfill as source for mobile phone
  assignee: yaara
  topic: deliveries
  status: On Hold
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1483
  title: Analyze Salutary March 2026 dataset for pipeline ingestion
  assignee: yaara
  topic: contacts
  status: On Hold
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

- key: ATB-1486
  title: oncall || website_keywords coverage gap
  assignee: yaara
  topic: other
  status: On Hold
  parent_epic: 
  labels: []
  estimation: 1
  last_synced: 2026-04-05T21:43:10+03:00

## Ticket Block Template

```yaml
- key: ATB-0000
  title: Example task title
  assignee: ron
  topic: tech_debt
  status: To Do
  parent_epic: ATB-0001 Example epic
  labels: [example, cleanup]
  estimation: 1
  last_synced: 2026-04-05T12:00:00+03:00
```
