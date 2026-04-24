# Atlas ETL inventory

Generated: 2026-04-17

## Goal

Build a working Atlas ETL inventory for future observability work, with a hard split between:

- active during the recent year
- paused but still relevant
- totally legacy / archived / replaced

Recent-year window used here: **2025-04-17 → 2026-04-17**.

## Locked scope

Atlas-default people:

- Itai Dagan
- Rani Khoury
- Yaara Yona
- Danielle Gan
- Sarah Levitz
- Tal Waldman
- Noa Gordon
- Itamar Avigdori
- Daniel Kuv
- Tamir Shorshy

Mixed-scope people, included only with Atlas-specific evidence:

- Ron Yehezkel
- Itamar Fradkin
- Gur Ronen
- Avshalom Chai
- Yossi Golan

Included domains:

- contacts
- EDS / entities / firmographics
- business catalog
- partner service logs
- downstream deliveries
- Atlas support jobs tightly coupled to those flows

## Main sources used

- `tube-projects` Terraform + project files
- `atlas-jobs` legacy/manual project files
- live Databricks jobs + completed runs
- Slack alert history/search
- limited Jira sampling for ATB context

## Alert-channel timeline

### Current routing

- **start / success** → `#atlas-on-going`
- **failure** → `#issues-data`

Evidence:

- `slack_conversations_history(channel_id="#atlas-on-going", limit="30d")`
- `slack_conversations_history(channel_id="#issues-data", limit="30d")`
- `git show --stat --format=fuller eaaa0216b`

### Historical / deprecated routing found

Observed in git or Slack search during the recent-year window:

- `#alerts-tube`
- `#data_deliveries` (via `data_deliveries_alerts` bot)
- `#tube-notifications` / `data_deliveries_alerts` references in old Terraform routing

Cutover commit:

- `eaaa0216b` — `chore(terraform): consolidate notification destinations to #issues-data and #atlas-on-going (#1625)`
- Commit date: **2026-04-14 19:44 Israel time**

Practical takeaway:

- before 2026-04-14, Atlas run notifications were fragmented across old channels/bots
- after 2026-04-14, Atlas notifications are much easier to observe centrally

## Inventory snapshot

Canonical live job names observed after de-duping same-name recreated jobs: **260**

| Status | Count |
|---|---:|
| Active scheduled | 24 |
| Active manual / on-demand | 55 |
| Paused but relevant | 2 |
| Legacy | 148 |
| Dev / test | 22 |
| Ambiguous | 9 |

Domain split:

| Domain | Count |
|---|---:|
| EDS | 110 |
| Contacts | 51 |
| Delivery | 40 |
| Business catalog | 15 |
| Contacts ops | 15 |
| Partner service logs | 6 |
| Funding rounds | 3 |
| Events | 3 |
| Adjacent technographics | 4 |
| Other | 13 |

## What is definitely active now

### Active scheduled

| Domain | Job | Last run (Israel) | Notes |
|---|---|---|---|
| Delivery | DELIVERY_BOT_commonroom | 2026-04-01 11:29 | current Terraform-managed delivery |
| Delivery | DELIVERY_BOT_i360 | 2026-03-30 23:12 | current Terraform-managed delivery |
| Delivery | DELIVERY_BOT_madison_logic | 2026-04-14 20:57 | current Terraform-managed delivery |
| Delivery | DELIVERY_BOT_surfe | 2026-03-19 18:01 | current Terraform-managed delivery |
| Delivery | DELIVERY_BOT_bombora | 2026-03-01 06:00 | legacy-live scheduled delivery |
| Delivery | DELIVERY_BOT_Clay | 2026-03-25 06:00 | legacy-live scheduled delivery |
| Delivery | DELIVERY_BOT_Clearitty_tech | n/a in captured run slice | scheduled but no recent completed run captured |
| Delivery | DELIVERY_BOT_connectbase | 2026-03-01 02:00 | legacy-live scheduled delivery |
| Delivery | DELIVERY_BOT_digital_envoy | 2026-04-16 12:36 | scheduled delivery |
| Delivery | DELIVERY_BOT_onfire | 2026-04-01 07:00 | legacy-live scheduled delivery |
| Delivery | DELIVERY_BOT_swordfish | 2026-04-05 15:49 | legacy-live scheduled delivery |
| Delivery | DELIVERY_BOT_vi | 2026-03-20 06:00 | legacy-live scheduled delivery |
| Delivery | DELIVERY_BOT_Wappalyzer_contacts | 2026-04-01 13:00 | scheduled delivery |
| Delivery | DELIVERY_BOT_Wappalyzer_crunchbase | 2026-04-01 03:00 | scheduled delivery |
| Delivery | DELIVERY_BOT_Wappalyzer_ffi | 2026-04-01 03:00 | scheduled delivery |
| Delivery | DELIVERY_BOT_Wappalyzer_firmo | 2026-04-01 03:00 | scheduled delivery |
| Delivery | DELIVERY_BOT_Wappalyzer_glassdoor | 2026-04-01 03:00 | scheduled delivery |
| Delivery | DELIVERY_BOT_Wappalyzer_wft_by_company_department | 2026-04-01 03:00 | scheduled delivery |
| Delivery | DELIVERY_BOT_Wappalyzer_wft_by_employee_level | 2026-04-01 03:00 | scheduled delivery, last run failed |
| Delivery | DELIVERY_BOT_Wappalyzer_wft_by_workforce_demographics | 2026-04-01 03:00 | scheduled delivery, last run failed |
| Funding rounds | Funding Rounds Collector Workflow | 2026-04-17 07:00 | current Terraform-managed Atlas notebook job |
| Partner service logs | partner service logs - unity - full flow | 2026-04-17 20:02 | current Terraform-managed orchestrator |
| Monitoring | Check indexes are updated in elastic | 2026-04-16 14:00 | current Terraform-managed monitor, migrated from atlas-jobs |
| Adjacent | technographics -OLD DONT RUN | 2026-03-22 03:15 | flagged scheduled but clearly smells legacy; keep out of observability priority list |

### Active manual / on-demand — current Terraform-managed and high-confidence

These are current code-defined jobs that had recent-year activity but are not on a live schedule.

| Domain | Job | Last run (Israel) | Notes |
|---|---|---|---|
| Business catalog | business catalog opensearch writer-unity | 2026-04-16 13:31 | current writer |
| Business catalog | business-catalog-labels-unity | 2026-03-31 13:13 | current labels writer |
| Partner service logs | sr - partner service logs - unity | 2026-04-17 20:18 | current silver/dbt job |
| Delivery | tube-writer | 2026-04-16 11:21 | current PG writer for contacts_united_for_pc_and_bcd |
| EDS | gold-eds-writer | 2026-03-30 23:04 | current EDS writer |
| EDS | non_eds_domain_scraper | 2026-04-14 19:45 | current supporting scraper, used by Madison Logic |
| EDS | operations-eds-opensearch-writer | 2026-03-31 00:15 | current EDS/OpenSearch writer |
| EDS | orchestrator-eds-main-pipeline | 2026-03-29 20:17 | current orchestrator |
| EDS | orchestrator-eds-gold-runs | 2026-03-30 22:55 | current orchestrator |
| EDS | silver-eds-entity-linking | 2026-03-27 00:24 | current core step |
| EDS | silver-eds-entities | 2026-03-30 09:17 | current core step |
| EDS | silver-eds-post-enrichers | 2026-03-29 23:54 | current core step |
| EDS | silver-eds-eac-firmo | 2026-03-30 22:55 | current core step |
| EDS | silver-eds-pre-enricher-linkedin | 2026-03-26 16:28 | current pre-enricher |
| EDS | silver-eds-asset-linkedin-to-urn | 2026-03-26 23:41 | current supporting asset |
| EDS | silver-eds-asset-manual-name-linkedin-mapping | 2026-03-26 16:33 | current supporting asset |
| EDS | silver-eds-asset-related-urns | 2026-03-26 23:29 | current supporting asset |
| EDS | silver-eds-asset-serp-to-linkedin | 2026-03-26 23:25 | current supporting asset |
| Events | Events Writer Job | 2026-04-17 07:32 | current event writer |
| Monitoring | dbt-jobs_monitoring | 2026-04-16 12:03 | shared monitor used by Atlas jobs |
| Monitoring | credits_mix_panel_writer | 2026-04-17 20:23 | current partner-service-logs support job |
| Business catalog / adjacent | tech_stack__technographics_v2-dbt-job | 2026-03-01 15:24 | current job, but better treated as Atlas-adjacent |

### Active manual / on-demand — live jobs not currently anchored in the current Terraform slice

These matter operationally because they still ran within the recent-year window.

| Domain | Job | Last run (Israel) | Notes |
|---|---|---|---|
| Business catalog | business-catalog-sr-unity | 2026-04-16 10:59 | still active; current code comments say migration is still incomplete |
| Business catalog | business_catalog-dbt-job | 2026-04-16 10:59 | live/manual dbt job |
| Contacts | contacts-united-for-pc-bcd-unity | 2026-04-13 22:38 | active manual |
| Contacts | contacts_data_validations-dbt-job | 2026-04-13 22:01 | active manual |
| Contacts | bc_data_validations-dbt-job | 2026-04-16 11:27 | active manual |
| Contacts | contacts_starter__contacts_starter-dbt-job | 2026-04-13 20:36 | active manual |
| Contacts | contacts_united__contacts_united_base-dbt-job | 2026-04-13 18:11 | active manual |
| Contacts | contacts_united__for_pc_and_bcd-dbt-job | 2026-04-13 20:36 | active manual |
| Contacts | projects__contacts_workforce_changes-dbt-job | 2026-04-13 22:02 | active manual |
| Contacts | projects__contacts_workforce_trends-dbt-job | 2026-04-13 20:38 | active manual |
| Contacts | sr-contacts workforce-changes-unity | 2026-04-14 17:03 | active manual |
| Contacts | sr-contacts workforce-trends-unity | 2026-04-16 11:16 | active manual |
| Contacts | sr-contacts-starter-unity | 2026-04-13 22:00 | active manual |
| Contacts | sr-contacts-united-base-v2-unity | 2026-04-13 18:10 | active manual |
| Contacts | E2E - contacts | 2026-04-09 21:50 | active but likely validation-only |
| Contacts | gd-contacts-workforce-changes | 2026-04-14 17:03 | active manual |
| Contacts | gd-contacts-workforce-trends | 2026-02-16 22:41 | active manual |
| Contacts | gd-contacts-workforce-trends-departmental | 2026-02-16 22:41 | active manual |
| Contacts | labels-contacts-company-industry | 2026-03-11 10:26 | active manual |
| Contacts | labels-contacts-interests | 2026-03-11 10:55 | active manual |
| Contacts | labels-contacts-skills | 2026-03-11 10:48 | active manual |
| Contacts ops | automated email validation - contacts - unity | 2026-03-11 14:30 | active manual |
| Contacts ops | Email Validation - Reacher | 2026-04-05 13:30 | active manual |
| Contacts ops | Revenue Base email validation | 2026-04-05 19:38 | active manual |
| Contacts ops | check status - Revenue Base email validation | 2026-04-05 19:51 | active manual |
| Contacts ops | Handle single privacy request | 2026-04-17 06:52 | active manual support |
| Contacts ops | Privacy data extraction | 2026-04-13 14:23 | active manual support |
| Delivery | data_deliveries__bombora-dbt-job | 2026-03-01 06:00 | active manual delivery dbt job |
| Delivery | data_deliveries__connectbase_us-dbt-job | 2026-03-01 02:00 | active manual delivery dbt job |
| Delivery | commonroom-us-silver-unity | 2026-02-18 10:26 | active manual historical delivery job |

### Paused but still relevant

| Domain | Job | Last run (Israel) | Notes |
|---|---|---|---|
| Delivery | DELIVERY_BOT_i360_contacts | 2026-03-01 06:00 | paused now, but still ran in the recent-year window |
| Delivery | DELIVERY_BOT_i360_companies | 2026-03-01 06:00 | paused now, but still ran in the recent-year window |

## Current Terraform definitions that look inactive / legacy in the recent-year window

This is the most important observability takeaway: **current code presence does not mean operationally active**.

Current code-defined jobs that did **not** show up as active in the recent-year run scan include:

- `privacy-dbt-job`
- `dbt-eds-pre-enrichers`
- `dbt-eds-hybrid-ingestion`
- `google_places__hybrid_eds_ingestion-dbt-job`
- `serp__serp_for_eds-dbt-job`
- `silver-eds-source-dunbledore`
- `silver-eds-source-google-places-hybrid`
- `silver-eds-source-linkedin-companies`
- `silver-eds-source-public-companies`
- `silver-eds-source-rar`
- `silver-eds-source-crunchbase`
- `silver-eds-pre-enricher-creditsafe`
- `silver-eds-pre-enricher-crunchbase`
- `silver-eds-pre-enricher-dunbledore`
- `silver-eds-pre-enricher-google-places`
- `silver-eds-pre-enricher-public-companies`
- `silver-eds-pre-enricher-rar`
- `silver-eds-asset-dunbledore-deduped`
- `silver-eds-asset-google2naics`
- `silver-eds-asset-linkedin-to-naics`
- `silver-eds-asset-noe-rev-stats`
- `silver-eds-asset-url-mapping`
- `silver-eds-categories-mapping`
- `silver-eds-categories-mapping-full`
- `silver-eds-for-serp`
- `silver-eds-hybrid-enricher`
- `silver-eds-hybrid-ingestion`
- `silver-eds-hybrid-operating-score`
- `silver-eds-impute-noe-revenue`
- `silver-eds-name-similarity`
- `silver-eds-post-enrichers-nol-noe-rev`
- `test-eds-sanity-checks`

Interpretation:

- some of these are genuinely dormant
- some are replaced by newer orchestrated/manual flows with different names
- some may only run ad hoc and simply did not appear in the last-year completed-run slice

For observability bootstrapping, these should **not** be treated as Tier-1 active pipelines until confirmed.

## Legacy families worth treating as replaced or low-priority

### EDS legacy families

Large legacy cluster observed around:

- `EDS2:*`
- `[ARCHIVED] silver-eds-*`
- `[ARCHIVED] eds-assets-*`
- `eds-*` old bronze / categories / writer names
- `update-eds-alias`

Examples:

- `[ARCHIVED] EDS2: from source to enrichment`
- `[ARCHIVED] EDS2: gold runs`
- `[ARCHIVED] silver-eds-entities`
- `[ARCHIVED] silver-eds-entity-linking`
- `[ARCHIVED] silver-eds-post-enrichers`
- `[ARCHIVED] silver-eds-pre-enricher-*`
- `[ARCHIVED] eds-assets-*`
- `eds2`
- `eds2-seo`
- `EDS_WRITER`
- `EDS_INDEX_S3_TO_ES`

### Contacts legacy families

Large legacy cluster observed around:

- old contacts label writers
- old workforce writers
- old contacts OpenSearch writers
- `contacts_overwrite`

Examples:

- `contacts starter opensearch writer - old`
- `contacts-labels`
- `contacts_overwrite`
- `gd-contacts-starter-es-prod`
- `Gold writer for new urn for contacts - TEMP`
- `labels-contacts-company-*`
- `labels-contacts-loc-*`
- `labels-contacts-job-titles`
- `labels-contacts-experience`

### Business catalog legacy families

Examples:

- `business-catalog sr - old`
- `business-catalog-es-prod-gold`
- `business-catalog-labels-old`
- `business-catalog-prod-gd-eac-old`
- `business-catalog-prod-gd-eac-unity`
- `business-catalog-seo-silver`
- `old - business catalog opensearch writer`

### Delivery legacy families

Examples:

- `DELIVERY_BOT_CarbonArc_*`
- `DELIVERY_BOT_Cognism_firmo`
- `[ARCHIVED] assets_data_imputation-sr-unity`

## Dev / test / clone bucket

Keep these out of production observability unless you explicitly want non-prod coverage.

Examples found:

- `[dev rani_khoury] DELIVERY_BOT_madison_logic`
- `Clone of DELIVERY_BOT_commonroom`
- `DELIVERY_BOT_i360_test`
- `[dev avshalom_chai] non_eds_domain_scraper`
- `[dev rani_khoury] non_eds_domain_scraper`
- `eds-writer-test`
- `Test Only - EDS Gold runs`
- `Test Events Writer Job - json schema`
- `Clone of Funding Rounds Collector Workflow(DEV)`
- `Privacy Test`

## Ambiguous bucket

These exist, but I would not wire them into the first observability slice yet:

- `contactout-dbt-job`
- `contactout-emails-bz`
- `contactout-profiles-bz`
- `data_coverages-dbt-job`
- `E2E - contactout`
- `generic_event_filters`
- `all labels opensearch writer`
- `sr-provider-contactout`

## High-priority observability bootstrap list

If I were wiring observability first, I would start here:

1. `partner service logs - unity - full flow`
2. `sr - partner service logs - unity`
3. `Funding Rounds Collector Workflow`
4. `Events Writer Job`
5. `Check indexes are updated in elastic`
6. `tube-writer`
7. `business-catalog-sr-unity`
8. `business catalog opensearch writer-unity`
9. `business-catalog-labels-unity`
10. `DELIVERY_BOT_commonroom`
11. `DELIVERY_BOT_i360`
12. `DELIVERY_BOT_madison_logic`
13. `DELIVERY_BOT_surfe`
14. `contacts_united__contacts_united_base-dbt-job`
15. `contacts_united__for_pc_and_bcd-dbt-job`
16. `contacts_starter__contacts_starter-dbt-job`
17. `contacts_data_validations-dbt-job`
18. `projects__contacts_workforce_trends-dbt-job`
19. `projects__contacts_workforce_changes-dbt-job`
20. `gold-eds-writer`
21. `orchestrator-eds-main-pipeline`
22. `orchestrator-eds-gold-runs`
23. `silver-eds-entities`
24. `silver-eds-entity-linking`
25. `silver-eds-post-enrichers`

## Migration markers from git history

- `3ba11f72c` — `Migrate atlas notebooks and jobs (#1364)`
  - imported Atlas notebooks/jobs into `tube-projects`
  - moved funding rounds, updated-index, events-writer, privacy, partner-service-logs and related pieces into repo-managed Terraform/notebooks

- `eaaa0216b` — `chore(terraform): consolidate notification destinations to #issues-data and #atlas-on-going (#1625)`
  - unified Atlas job alert routing

- `e85a944fe` — `Tube Writer (#1565)`
  - current `tube-writer` history anchor

- `caa7522db` — `feat(commonroom): add Terraform project for CommonRoom data delivery job (#1490)`
  - current CommonRoom delivery history anchor

## Caveats

- Slack history is partially retention/search dependent.
- Databricks run scan only used completed runs; jobs with only failed-internal attempts or no surfaced completion in the recent-year window may look older than they are.
- Some names exist as recreated jobs under multiple IDs; this file de-dupes by canonical name first.
- Some current Terraform definitions are clearly present in code but not active in practice.

## Exact commands / tool calls used

- `git show --stat --format=fuller eaaa0216b`
- `git show --stat --format=fuller 3ba11f72c`
- `git log --oneline --since="2025-04-17" -- "terraform/notebooks/operations/tube_writer/main.tf"`
- `git log --oneline --since="2025-04-17" -- "terraform/notebooks/projects/funding_rounds/main.tf"`
- `git log --oneline --since="2025-04-17" -- "terraform/projects/data_deliveries/commonroom/main.tf"`
- `databricks api get "/api/2.2/jobs/list?limit=100"` with pagination
- `databricks api get "/api/2.2/jobs/runs/list?limit=26&completed_only=true"` with pagination
- `slack_conversations_history(channel_id="#atlas-on-going", limit="30d")`
- `slack_conversations_history(channel_id="#issues-data", limit="30d")`
- `slack_conversations_search_messages(search_query="\"run has failed\"", filter_date_after="2025-04-17")`
- `slack_conversations_search_messages(search_query="\"run has started\"", filter_date_after="2025-04-17")`
- `slack_conversations_search_messages(search_query="\"run has completed successfully\"", filter_date_after="2025-04-17")`
- targeted `Read`, `Glob`, and `Grep` calls over `tube-projects` and `atlas-jobs`
