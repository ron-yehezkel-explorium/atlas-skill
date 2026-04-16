# Interview Process — Senior Data Engineer, Atlas Team

## Step 1: CV Review

**By:** Ilana, Ron

Review CV and decide whether to proceed.

---

## Step 2: Phone Screen

**By:** Hadar
**Format:** Phone call (~20 min)

Short professional conversation with a small technical question to filter out clearly non-fit candidates before investing interview time.

---

## Step 3: Technical Screen (Zoom)

**By:** Yaara
**Duration:** 30 minutes
**Format:** Zoom

Intensive filter to verify minimum seniority-level qualifications. Must pass a clear threshold to proceed to the in-person stage.

| Time | Block |
|---|---|
| 5 min | **Intro** — Brief overview of Explorium, the Atlas team, and the role |
| 10 min | **Candidate background** — Let them walk through their experience and current role |
| 15 min | **Technical questions** — Three quick questions (~5 min each). Candidate should answer confidently and from experience, not textbook definitions. See questions below |

**Question 1 — Data Modeling:**
"You're receiving data from multiple sources with overlapping schemas. How do you approach modeling the unified dataset? When would you denormalize vs. keep it normalized?"
*Minimum bar: Articulates trade-offs clearly (query performance vs. storage/consistency), mentions a real scenario they handled. Red flag: only knows one approach or gives a purely theoretical answer.*

**Question 2 — Production Ownership:**
"You deploy a new pipeline on Friday. Monday morning you find it produced duplicate records downstream. Walk me through what you do."
*Minimum bar: Structured investigation (check source data, transformation logic, idempotency, MERGE behavior). Mentions how they'd prevent recurrence (tests, monitoring). Red flag: jumps to "rerun the pipeline" without understanding root cause.*

**Question 3 — Spark/Databricks:**
"You have a Spark job that's running 3x slower than expected. What are the first things you look at?"
*Minimum bar: Mentions data skew, shuffle, partition sizing, or Spark UI. Speaks from experience with specific examples. Red flag: can't go beyond "add more clusters" or gives generic answers.*

---

## Step 4: In-Person Technical Interview

**By:** Ron + team member
**Duration:** 1.5 hours
**Format:** On-site, face-to-face

The core evaluation — technical depth, problem-solving approach, and product/business orientation.

| Time | Block |
|---|---|
| 10 min | **Company & team** — Deeper dive into Explorium, the Atlas team, stack, and what we're building |
| 20 min | **Candidate deep dive** — Walk through their background, a significant project they led, and the technical decisions they made |
| 60 min | **Live challenge** — Hands-on data engineering task in a Databricks notebook. Tests both technical execution and product thinking. See challenge below |

**Challenge: Data Source Integration**

The candidate receives a Databricks notebook with:
- A raw dataset of company records from a simulated external data provider (messy: duplicates, missing fields, inconsistent formats)
- A clean internal reference dataset

**The task:** Build a pipeline in the notebook that ingests the external data, cleans it, matches/merges it against the internal dataset, and produces a unified output table ready for downstream consumers.

**How it works:**
1. **(~10 min) Requirements & design** — Before writing code, the candidate should ask questions: Who consumes this data? What's the freshness requirement? How often does the source update? What happens when records conflict? This is where product and business thinking surfaces naturally — do they clarify the problem or just start coding?
2. **(~40 min) Implementation** — Live coding in the notebook. SQL, Python, PySpark — their choice. They should handle deduplication, schema alignment, data quality checks, and the merge logic.
3. **(~10 min) Production readiness** — Walk through: how would you deploy this? What monitoring and tests would you add? What would break at 10x scale? How do you think about cost?

**What we're evaluating:**

| Signal | What to look for |
|---|---|
| Product thinking | Asks about consumers, SLAs, and business context before coding |
| Data quality instinct | Explores the data first, doesn't assume it's clean |
| Technical depth | Clean, working code — handles edge cases, uses appropriate Spark/SQL patterns |
| Modeling decisions | Justified choices on schema, dedup strategy, merge approach |
| Production mindset | Thinks about monitoring, testing, failure modes, cost |

*Red flag: Jumps straight to implementation without asking a single question about the use case.*

---

## Step 5: Leadership & Final Interviews

**By:** Gur, Lonny, Ilana

Final round with leadership. Format and focus at their discretion.

---

## Decision

Debrief after all steps complete. Any interviewer can raise a blocker. Ron makes the final call.
