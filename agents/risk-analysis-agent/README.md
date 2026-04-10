# Resilient Supply Chain Risk Analysis Agent

## 🎯 The Mission
**What:** An autonomous, multi-sensor AI agent that performs real-time, quantified risk analysis on global supply chain components — cross-referencing satellite fire data, weather forecasts, geopolitical news, and historical risk profiles to score supplier threats before they become stockouts.

**The Problem:** SMB manufacturers operate in a reactive "firefighting" mode — they discover a supplier disruption (port strike, factory fire, typhoon) only after it has already impacted their production timeline. By then, the shortfall is live, the deadline is missed, and the scramble for alternatives costs 3–5x more than proactive sourcing would have.

**The Solution:** Moves from reactive incident response to a **proactive, agent-led resilience pipeline**. The Scout agent ingests structured supply alerts, deploys four live data sensors simultaneously, applies a weighted risk formula, and routes output either to a human reviewer (CRITICAL) or auto-approval (NOMINAL/ELEVATED) — all before a human would have even opened their inbox.

---

## 🧠 Product Strategy & "Shielded" Logic

* **The "Why" (ROI):** The cost of a single missed stockout event for an SMB manufacturer — lost production, emergency sourcing, expedited freight — routinely exceeds $50K–$200K. This agent converts that unpredictable cost into a predictable, sub-$1/analysis intelligence operation. The ROI is measured in **prevented disruptions**, not hours saved.

* **The "Causal Reasoning" Metric:** The agent does not just flag events — it chains them to operational impact. A typhoon warning only matters if it affects the `projected_stockout_date`. The reasoning chain enforces: *Observation → Causal Impact on deadline and volume → Risk Score*. A storm in a region that doesn't touch the transit route registers as NOMINAL. This eliminates alert fatigue.

* **Edge Case Handling:**
  * **API Rate Limiting (429 errors):** All four external data tools (`NASA FIRMS`, `GDELT`, `NewsData.io`, `Open-Meteo`) are configured with `onError: continueRegularOutput`. If a tool is throttled, the agent notes the gap, applies the Precautionary Principle (leans Elevated rather than Nominal on any sensor anomaly), and continues. No single API failure halts the pipeline.
  * **Malformed NASA Bounding Box:** The FIRMS API returns a `400 Invalid area coordinate` error if coordinates are reordered. The system prompt explicitly enforces passing the `bounding_box` string EXACTLY as received — a lesson learned in testing.
  * **Bilingual / Cross-Sensor Inference:** If GDELT is unavailable but Open-Meteo shows `>25mm precipitation`, the agent applies a baseline `Lead Time Risk: 5` and `Geographic Risk: 4` — cross-sensor validation that prevents zero-risk defaults when primary tools are down.
  * **Backup Supplier Vetting (Agent C path):** Alerts sourced from `agent_c` represent backup supplier verification. These follow an **Auto-Approval path regardless of risk score** — the human-in-the-loop gate is bypassed because the decision has already been made to source from this supplier; the Scout is confirming it's not worse than the current bottleneck.

* **Guardrails & Privacy:**
  * **HITL Gate:** Any risk score `≥ 7.0` from `agent_a` alerts triggers a mandatory Human-in-the-Loop flag before the result is written to the database. Auto-approval only flows for NOMINAL/ELEVATED scores.
  * **Zero-Hallucination Enforcement:** The agent is forbidden from reporting a risk without a traceable source link. No citation = "No Risk Detected." This is enforced in the system prompt and validated by the structured output parser.
  * **Structured Output Contract:** The `Risk Assessment JSON Output Parser` node enforces a strict schema with `autoFix: true` — malformed LLM outputs are automatically corrected before reaching downstream systems.
  * **Credential Isolation:** API keys for NewsData.io and NASA FIRMS are stored as `{{PLACEHOLDER}}` variables. All n8n credential references use the encrypted credential store.

---

## 🛠️ Technical Stack

| Layer | Technology | Prompt Logic |
|---|---|---|
| **Orchestration** | n8n Cloud | — |
| **Core AI Agent** | OpenAI GPT-4o-mini (`@n8n/n8n-nodes-langchain.agent`) | [`prompts/scout-agent-instructions.md`](prompts/scout-agent-instructions.md) — full reasoning chain, tool thresholds, guardrails |
| **Weather Sensor** | Open-Meteo API (free, no key required) | Typhoons, floods, heat stress, transit disruptions |
| **Fire/Thermal Sensor** | NASA FIRMS VIIRS SNPP NRT | Satellite fire detection near supplier coordinates |
| **Geopolitical Sensor** | GDELT Project API | Global media monitoring for strikes, protests, unrest |
| **News Sensor** | NewsData.io API | Localized supply chain news with citable links |
| **Risk Scoring** | Custom JS Tool (weighted formula) | Geo 20% · Availability 30% · Lead Time 30% · Substitutability 20% |
| **Memory — Session** | n8n Buffer Window Memory (keyed by `alert_id`) | Prevents redundant API calls within a session |
| **Memory — Long-Term** | In-Memory Vector Store + OpenAI Embeddings | Historical risk profiles by supplier and location |
| **Output Parser** | Structured JSON Output Parser (`autoFix: true`) | Schema enforcement on all LLM output |
| **Data Persistence** | Google Sheets (`ResilientSupplyAgentDatabase`) | Audit log of all risk assessments and HITL decisions |
| **Trigger** | Google Sheets Trigger (weekly poll, `rowAdded` event) | New alert row → triggers full analysis pipeline |
| **API Endpoint** | Webhook `GET /risk-analysis-results` | Exposes risk results to external consumers |

**Architecture — Three Flows:**
1. **Analysis Flow** — Google Sheets Trigger → Loop Over Items → Scout Agent (4 sensors + Vector Store) → Risk Calculation Tool → HITL Gate → Split Out → Google Sheets log
2. **Auto-Approval Path** — Risk Score `< 7` OR `alert_from = agent_c` → Mark Auto-Approved → Google Sheets log
3. **Results API** — Webhook GET → Google Sheets read → Respond with JSON

---

## 📊 Performance & Insights

* **Multi-Sensor Resilience:** The most critical architectural decision was designing for partial data availability from the start. Production API environments — especially GDELT and NASA FIRMS — regularly return `429` rate limit errors at scale. The pipeline degrades gracefully: each sensor failure is logged, cross-sensor inference fills the gap, and the Precautionary Principle ensures no false NOMINAL scores slip through.

* **Causal Reasoning vs. Pattern Matching:** Early versions scored risk based on event proximity alone. The breakthrough was tying every risk dimension explicitly to `projected_stockout_date` and `shortfall_qty`. A `magnitude 6.0` earthquake 200km from a supplier on a 90-day lead time is NOMINAL. The same event with a 3-day deadline is CRITICAL. The agent reasons about *operational impact*, not just *event existence*.

* **Historical Weighting (+2 Adjustment):** The Vector Store's predictive weighting adds `+2` to the risk score when a current threat matches a documented historical failure pattern for that supplier or region. This transforms the Vector Store from a log into a live risk amplifier.

* **HITL Gate Precision:** The `≥ 7.0` threshold for human review was calibrated to minimize both false positives (alert fatigue) and false negatives (missed critical events). The `agent_c` bypass ensures backup supplier vetting doesn't clog the human review queue.

---

## 🎥 Demo

> *Demo link — Loom walkthrough coming soon.*

---

## 🚀 Deployment & Scalability

1. **Import:** Load `workflow.json` from this directory into your n8n instance.
2. **Configuration:** Replace all `{{PLACEHOLDER}}` tags with your credentials (see [`docs/setup-guide.md`](docs/setup-guide.md) for the full variable map).
3. **Credentials Required:**
   * OpenAI API Key
   * NewsData.io API Key
   * NASA FIRMS API Key
   * Google Sheets OAuth2 (two accounts: write + read)
   * Google Sheets Trigger OAuth2
4. **Data Setup:** Create your `ResilientSupplyAgentDatabase` Google Sheet with a `Test_Alerts` tab (input) and `Risk Analysis Results` tab (output). See setup guide for column schema.
5. **Environment:** Designed for **n8n Cloud**. Compatible with self-hosted n8n.
6. **Scalability Path:** The Loop Over Items node processes alerts in batches. Scale by increasing the Google Sheets Trigger poll frequency or replacing with a webhook trigger for real-time ingestion. The stateless-per-alert architecture supports horizontal parallelism with no workflow changes.
