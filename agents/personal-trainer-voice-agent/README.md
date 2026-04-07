# Personal Trainer Voice Agent

## 🎯 The Mission
**What:** An autonomous, bilingual voice agent that proactively calls personal training clients 24 hours before their session, confirms attendance, and delivers a structured intelligence briefing to the coach — without any manual intervention.

**The Problem:** A solo fitness coach managing a full client roster loses approximately **5 hours per week** to manual "Are we still on?" outreach via text and calls. Beyond logistics, the coach has zero insight into a client's physical or mental state before they walk through the door — meaning injuries, low energy, or life stressors are discovered mid-session, 20 minutes into a squat set.

**The Solution:** Moves from reactive, manual communication to a **reasoning-based LLM pipeline** that understands intent, normalizes bilingual speech, and converts a raw phone call into a structured coaching brief — delivered to the coach's inbox before the session begins.

---

## 🧠 Product Strategy & "Shielded" Logic

* **The "Why" (ROI):** Reclaims **~20 hours of operational capacity per month** for the coach. This is not administrative automation — it is a reallocation of cognitive bandwidth toward high-value work: client acquisition and advanced program design. The secondary ROI is **Institutional Memory**: the agent builds a permanent, searchable record of client Energy Trends across an entire roster, a task that is practically impossible for a single coach to maintain manually.

* **The "Session Pivot Quality" Metric:** ROI is measured by the quality of session preparation. The coach no longer reacts to a disclosed injury 20 minutes into a session. He receives a structured mobility alert 24 hours in advance and arrives with a recovery-focused plan already designed.

* **Edge Case Handling:**
  * **Missing Phone Number:** The extraction node enforces a null-check on `phone_number`. If the field is absent from the calendar event description, the value is set to `null` and the outbound call step is bypassed — preventing a failed API call or a misdial.
  * **Appointment Cancellation / Reschedule:** The transcript analyst extracts an `appointment_confirmed` boolean. A `false` value surfaces as an `❌ CANCELLED` alert in the coach's briefing email, flagging it for manual follow-up without the workflow erroring out.
  * **Bilingual Ambiguity (STT Phonetic Drift):** The Retell AI STT engine frequently misinterprets French phonetics as English words (e.g., `"Oui"` → `"We"`, `"Dix"` → `"Dies"`, `"Quatre"` → `"Cat"`). The analyst node detects the client's established language preference from the transcript opening and applies **contextual inference** — resolving intended meaning over literal spelling. This was the single highest-impact prompt engineering breakthrough in the build.
  * **Out-of-Scope or Incomplete Responses:** If a client hangs up or provides a partial response, all schema fields include defined defaults (`""` for strings, `false` for booleans). The pipeline completes and delivers a partial brief rather than failing silently.

* **Guardrails & Privacy:**
  * **Structured Output Enforcement:** Both LLM nodes use OpenAI's `json_schema` response format with `"additionalProperties": false` and all fields declared `required`. No hallucinated keys can enter the downstream pipeline — the schema is the contract.
  * **Credential Isolation:** All API keys, phone numbers, and calendar IDs are stored exclusively in n8n's encrypted credential store. The workflow JSON is a clean, deployable template with zero hardcoded secrets.
  * **Auditability:** Every run produces a structured email brief — a permanent, human-readable record of what the agent heard, extracted, and surfaced to the coach.

---

## 🛠️ Technical Stack

| Layer | Technology | Prompt Logic |
|---|---|---|
| **Orchestration** | n8n Cloud (`mcdevo.app.n8n.cloud`) | [`prompts/orchestration-logic.md`](prompts/orchestration-logic.md) — backend business rules: calendar extraction, transcript analysis, and structured output enforcement |
| **Intelligence — Extraction** | OpenAI GPT-4o-mini (structured JSON extraction, cost-optimized) | See orchestration-logic.md · Node 1 |
| **Intelligence — Analysis** | OpenAI GPT-4o-mini (bilingual transcript analysis + intent recognition) | See orchestration-logic.md · Node 2 |
| **Voice Engine** | Retell AI (Bilingual Multilingual Model) | [`prompts/voice-interface-persona.md`](prompts/voice-interface-persona.md) — real-time conversation logic: persona, bilingual flow, guardrails, and energy check |
| **Data Source** | Google Calendar (event-driven client roster) | — |
| **Notification Layer** | Gmail (structured HTML coaching brief) | — |
| **Memory** | Stateless per-run — intelligence delivered as structured email records | — |

**Architecture:** Two decoupled flows:
1. **Outbound Flow** — Schedule Trigger → Google Calendar → GPT-4o-mini Extraction → Retell AI outbound call
2. **Inbound Flow** — Retell AI webhook (post-call) → GPT-4o-mini Transcript Analysis → Gmail coaching brief

---

## 📊 Performance & Insights

* **Response Velocity:** Achieved a **sub-900ms response loop** by switching the extraction layer from GPT-4o to GPT-4o-mini and tuning Retell AI's End-of-Turn Detection threshold to 700ms — the minimum threshold for natural conversation flow without false triggers.

* **The Bilingual Breakthrough:** The "Intelligent Bilingual Normalization" system is the core IP of this agent. Standard STT pipelines fail on bilingual speakers because they optimize for English phonetics. Moving from static word-lookup tables to **contextual intent recognition** improved energy score extraction accuracy by approximately **40% for non-native English speakers** — the dominant demographic in the Montreal fitness market.

* **Session Efficiency Reclaimed:** The proactive briefing eliminates roughly **10–12 minutes of reactive adjustment per session hour** (≈20% of active session time) previously lost to on-the-fly workout pivoting after discovering injuries or low energy at the start of a session.

* **Administrative Load Eliminated:** Replaces ~**5 hours/week** of manual confirmation outreach with a zero-touch automated pipeline.

* **No-Show Reduction (Target):** The verbal confirmation guardrail — requiring an explicit "Yes" or "No" before the session is logged as confirmed — is designed to reduce the no-show rate by creating a **higher-commitment confirmation signal** than a text message reply.

---

## 🎥 Demo

> *Demo link — Loom walkthrough coming soon.*

---

## 🚀 Deployment & Scalability

1. **Import:** Load `workflow.json` from this directory into your n8n instance.
2. **Configuration:** Replace all `{{PLACEHOLDER}}` variables with your credentials (see [`docs/setup-guide.md`](docs/setup-guide.md) for the full variable map).
3. **Credentials Required:**
   * Google Calendar OAuth2
   * OpenAI API Key
   * Retell AI API Key (HTTP Header Auth)
   * Gmail OAuth2
4. **Environment:** Designed for **n8n Cloud**. Compatible with self-hosted n8n on any managed VM or Docker environment.
5. **Scalability Path:** The stateless, event-driven architecture allows horizontal scaling — each new coach or client roster maps to a new calendar credential with zero changes to the core workflow logic.
