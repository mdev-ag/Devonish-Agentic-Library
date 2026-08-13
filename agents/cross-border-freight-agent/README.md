# Cross-Border Freight Coordination Agent

*Client and contact names in this document and the associated workflow are anonymized per client confidentiality requirements. See [`docs/confidentiality-note.md`](docs/confidentiality-note.md).*

## 🎯 The Mission

**What:** A two-flow agentic pipeline that automates the full lifecycle of cross-border freight coordination for a logistics services client — from monthly shipping schedule ingestion through carrier outreach to Bill of Lading (BOL) generation.

**The Problem:** Monthly shipping schedules arrived as PDF/Excel files requiring manual data entry into tracking systems. Carrier outreach for each shipment was performed manually via email with no standardized process. Bill of Lading documents were generated manually by copying and filling Excel templates. No audit trail existed for carrier selection decisions, and no early-warning system existed for missed carrier confirmations before pickup deadlines — an estimated 60+ minutes of administrative work per monthly cycle, with zero tolerance for data loss.

**The Solution:** A human-in-the-loop agentic system that ingests the schedule, drafts carrier-specific outreach, and generates BOL documentation automatically — while keeping a human in control of every external communication and every carrier selection decision.

---

## 🧠 Product Strategy & Guardrail Logic

* **The "Why" (ROI):** Reduces a 60+ minute manual monthly cycle to sub-5 minutes of automated processing across 15 truck loads and 3 simultaneous carrier outreach drafts per shipment, with zero data loss and a full audit trail — while never removing the human from either the outreach or the carrier-selection decision.

* **Design principle — Supervised Autonomy over full autonomy:** The build deliberately uses two distinct human-in-the-loop (HITL) gates rather than one, trading a small amount of speed for incremental trust-building. Full end-to-end automation was technically possible earlier than it shipped — the extra gate was a product decision, not a technical limitation.

* **Edge Case Handling:**
  * **Duplicate file processing:** Every uploaded file is checked against a `source_file_id` idempotency key before processing begins, preventing duplicate shipment rows or duplicate carrier outreach on re-uploads.
  * **Extraction failures:** A dedicated schema-validation checkpoint catches missing fields, unparseable JSON, or empty shipment arrays before any downstream write — routed to an operator alert rather than failing silently.
  * **No carrier response:** The carrier-selection wait state has a 24-hour timeout that fires an escalation alert with resent approval links, rather than holding indefinitely with no visibility.
  * **Draft quality:** Every AI-generated carrier email is validated for required fields (carrier name, pickup date, reference number) before being placed in a draft — never sent automatically.

* **Guardrails & Privacy:**
  * **Structured Output Enforcement:** Both LLM agents operate under an explicit Data Contract (MIND Framework) — no hallucinated keys reach downstream systems.
  * **Zero silent failures:** Seven distinct validation checkpoints route every failure category to an operator alert.
  * **Human control over external communication:** AI-drafted carrier emails are never sent automatically — they land in a drafts folder for human review and send.

---

## 🛠️ Technical Stack

| Layer | Technology | Role |
|---|---|---|
| **Orchestration** | n8n Cloud | Two-flow pipeline: PDF ingestion (Flow 1) and daily carrier outreach + BOL generation (Flow 2) |
| **Intelligence — Extraction** | GPT-4o mini | Parses shipping schedule PDFs into structured shipment records |
| **Intelligence — Drafting** | GPT-4o mini | Generates carrier-specific outreach email drafts using the MIND framework |
| **Trigger — Flow 1** | Cloud storage polling trigger | Detects new shipping schedule uploads |
| **Trigger — Flow 2** | Scheduled cron trigger | Daily 3-business-day lookahead check |
| **Storage — Shipments** | Spreadsheet-based staging table | Central shipment record store, written by Flow 1, read by Flow 2 |
| **Storage — Templates** | Cloud storage | Carrier-specific BOL templates, copied and filled after carrier selection |
| **Communication — Drafts** | Email (draft-only) | First HITL gate — human reviews and sends every carrier outreach email |
| **Communication — HITL** | Email with webhook approval links | Second HITL gate — carrier selection via one-click approval |
| **HITL Mechanism** | Wait node + webhook resume | Pauses execution indefinitely until a carrier is selected; 24-hour timeout escalation |
| **Evaluation & Testing** | n8n native Evaluations + LLM-as-judge scoring | Tiered binary-gate, quality-score, and monthly APF metrics — see [`docs/evaluation-harness.md`](docs/evaluation-harness.md) |

**Architecture:** Two decoupled flows —
1. **Flow 1 (Ingestion):** Schedule detection → deduplication check → PDF extraction → schema validation → structured shipment records written to staging table
2. **Flow 2 (Outreach + BOL):** Daily lookahead → per-carrier draft generation → draft validation → HITL review → carrier selection (webhook) → BOL generation → status update

---

## 📊 Performance & Insights

* **Manual baseline:** 60+ minutes per monthly shipment schedule — manual PDF review, data entry, carrier outreach drafting, BOL generation.
* **Automated processing time:** Sub-5 minutes from schedule upload to carrier drafts created and the carrier-selection request delivered.
* **Shipments per cycle:** 15 truck loads extracted and staged per monthly schedule; 3 simultaneous carrier outreach drafts generated per qualifying shipment.
* **HITL gates:** 2 — draft review (Gate 1) and webhook carrier selection (Gate 2).
* **Validation checkpoints:** 7 — deduplication, extraction schema, draft validation, wait-timeout, plus three dedicated alert paths.
* **BOL generation time:** Seconds after carrier selection — fully automated once a human has chosen the carrier.

**Key architectural decision — webhook interrupt over polling:** The carrier-selection gate uses a Wait node with a webhook resume URL rather than polling a status field, eliminating API overhead and creating a clean execution boundary between outreach and BOL generation.

---

## 🎥 Demo

> *Demo link — coming soon.*

---

## 🚀 Deployment & Scalability

1. **Import:** Load `workflow.json` from this directory into your n8n instance.
2. **Configuration:** Replace all `{{PLACEHOLDER}}` variables with your own credentials and identifiers — see [`docs/setup-guide.md`](docs/setup-guide.md).
3. **Credentials Required:** Cloud storage (Drive-equivalent) OAuth2, Spreadsheet OAuth2, Email OAuth2, LLM API key.
4. **Environment:** Designed for n8n Cloud; compatible with self-hosted n8n.
5. **Scalability path:** Carrier configuration is defined as a modular array in the outreach flow — adding a new carrier or client route requires no changes to core workflow logic, only a config update. A comment in the workflow marks the migration path to a spreadsheet-based config table for further scale.
