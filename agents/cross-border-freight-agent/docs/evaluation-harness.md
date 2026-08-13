# Evaluation Harness — Cross-Border Freight Coordination Agent

Evaluation follows a tiered structure: binary gates first (cheap, fast, catch hard failures), LLM-as-judge scoring second (quality signal for client-facing demonstration), and rollup business metrics third (monthly ROI reporting). The guiding insight: n8n's native Evaluations feature tests extraction fidelity (did the agent read the document correctly?) while conversation/output fidelity for downstream artifacts (drafts, BOLs) is validated through the production validation-node chain itself.

---

## Tier 1 — Binary Gate Evals (Minimum Viable)

| Eval | What it checks | Method |
|---|---|---|
| **Extraction Completeness** | All 5 required fields present in extraction output (pickup date, delivery date, shipment details, client, origin/destination) | Run against 5 historical schedule documents. Pass/fail binary. |
| **Duplicate Row Prevention** | Each source file ID appears exactly once in the staging table after processing | Query the staging table after append; assert uniqueness. Binary. |
| **Email Draft Field Validation** | Draft contains carrier name, pickup date, and reference number | Assert after each drafting agent call. Catches hallucinated or blank required fields. |
| **Business-Day Logic Accuracy** | Date-shift logic returns the correct 3-business-day lookahead | 10 known date-pair test cases (input → expected output). Run before production and on any code change. |

---

## Tier 2 — LLM-as-Judge Evals (Client-Facing Quality Signal)

| Eval | What it checks | Method |
|---|---|---|
| **Email Draft Quality Score (1–5)** | Required fields present, professional tone, correct carrier name, pickup date matches source | A second LLM call scores each draft; scores logged to an audit sheet. Drafts below 3 flagged for human review. |
| **Extraction Faithfulness Score (1–5)** | Did the agent accurately extract what was in the source document without hallucinating? | A second LLM call compares extracted JSON against raw source text. Logged to audit sheet. |
| **Response Velocity Logging** | Agent call duration, tracked over time | Timestamp before/after each AI agent call. Tracks p50/p95 for monthly performance review. |

---

## Tier 3 — APF Dimensions (Monthly ROI Briefing)

| Dimension | Definition |
|---|---|
| **Effectiveness** | % of shipments processed end-to-end without manual intervention. Baseline established in first 30 days. |
| **Efficiency** | Wall-clock time from ingestion trigger to confirmed staging-table row, compared against the 60-minute manual baseline. |
| **Reliability** | Failure-mode breakdown by category (extraction failure, sheet conflict, hallucination, API timeout, wait-node timeout) — presented as a breakdown, not a single aggregate number. |
| **Trust** | Human override rate — how often a carrier draft is edited before being sent. A decreasing rate over time is read as the agent earning trust, not just running longer. |

---

## Why This Structure

Binary gates alone would miss quality regressions (a draft can pass every required-field check and still read poorly). LLM-as-judge alone is too expensive and slow to run on every execution and doesn't catch hard failures cheaply. Layering both, then rolling up into business-facing APF metrics, keeps engineering-level testing and client-facing ROI reporting sourced from the same underlying evaluation runs rather than two disconnected efforts.
