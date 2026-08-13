# Bloc — Personal AI Scheduling Agent

*Personal identifiers (names, emails, locations, specific project names) are anonymized throughout this document per personal privacy preference. See [`docs/privacy-note.md`](docs/privacy-note.md). Domain categories and all architectural/technical detail are unaltered.*

## 🎯 The Mission

**What:** A production-grade conversational scheduling agent that manages calendar events across 3 Google accounts and 7 sub-calendars through two interfaces (Telegram and n8n Chat), enforcing a defined set of behavioral priority rules with a strict human-in-the-loop confirmation model — the agent proposes, a human approves or rejects, nothing is created without explicit sign-off.

**The Problem:** Manually juggling three accounts and seven sub-calendars with competing priorities — client work, relationship time, gym, deep work, job search, admin, and a community project — created scheduling decisions that interrupted deep work 3–5x per day. No system enforced personal protection rules (sleep buffer, protected gym windows) beyond mental notes, and no memory accumulated from what had been approved or rejected before — every week started from scratch.

**The Solution:** A single conversational agent, unified across both interfaces, that enforces 12 behavioral rules automatically and logs every decision (approved, rejected, and why) as the foundation for a Phase 2 preference-learning layer.

**The meta-point:** This was built as a proof of concept applied to its own builder — the same production standards used for client work (MIND Framework, Glass Box logging, HITL gates, APF observability) were applied here first, not as a demo, but as infrastructure depended on daily.

---

## 🧠 Product Strategy & Architecture Decisions

* **Dual-trigger, single-agent architecture:** One agent node fed by two separate triggers (Telegram, n8n Chat), with routing handled downstream by an IF node. The alternative — two separate agent nodes — was rejected early because it would have created prompt drift between interfaces and doubled the maintenance surface. One prompt, one tool set, one memory context, two interfaces.

* **Two-layer memory:** Short-term (Window Buffer Memory, conversational context within a session) and long-term (a decision-logging table capturing every approval and rejection with event type, day, week, trigger source, and the full raw proposal). The long-term layer isn't used for anything yet — it's deliberately built as the training-data foundation for a Phase 2 reasoning layer, accumulating signal from day one rather than waiting until the reasoning layer exists to start collecting it.

* **Decision logging — two distinct routing strategies:**
  * **Approval logging is structural** — the act of reaching the logger node after a Send action *is* the approval signal. No output parsing required.
  * **Rejection logging is marker-based** — the agent appends a structured `[DECISION: rejected | reason: X | type: Y]` marker as the final line of its response on explicit rejection, which a downstream detector node parses via regex. This distinction (structural vs. marker-based routing for two logically opposite outcomes) was a deliberate design choice to keep the common path — approval — simple, while giving the rarer path — rejection — the structure needed to capture a reason.

* **Data isolation as a design principle, not an afterthought:** The decision-logging database lives in its own isolated project, separate from any client-data systems, specifically to avoid mixing personal scheduling data with client data — a hygiene risk if a client project is ever handed off or audited. Row Level Security was enabled from creation; service-role access only, anon key never used for writes.

* **Model selection — deliberate downgrade, not compromise:** The original build used a general-purpose frontier model. It was swapped to a smaller, cheaper model after hitting a rate-limit wall during multi-turn testing — and the swap turned out to be the *better* fit, not just a workaround: this agent's task is structured rule-following, not novel reasoning, so a smaller purpose-fit model at roughly a third of the cost showed no observed quality gap. An upgrade path back to a larger model is explicitly documented as a fallback if decision-quality gaps emerge on review — the decision was made on task-fit evidence, with a stated reversal condition, not treated as permanent.

---

## 🛠️ Technical Stack

| Layer | Technology | Detail |
|---|---|---|
| **Orchestration** | n8n Cloud | Dual-trigger, single-agent workflow |
| **LLM** | Claude Haiku 4.5 | Swapped from a larger general-purpose model after a rate-limit constraint surfaced it wasn't needed for this task |
| **Interfaces** | Telegram (mobile) + n8n Chat (desktop) | Unified logging regardless of trigger source |
| **Memory — short-term** | Window Buffer Memory (n8n LangChain node) | Conversational context within a session |
| **Memory — long-term** | Isolated database project, decision-log table | Every approval/rejection logged with event type, day, week, trigger source, raw proposal |
| **Calendar access** | Calendar API via 10 tool nodes | 3 read-all (one per account) + 3 create + 4 sub-calendar-specific reads, across 3 accounts / 7 sub-calendars |
| **Credential security** | Service-role key only; RLS enabled from creation | Anon key never used for writes |
| **Evaluation** | Behavioral decision log + structural rule-adherence checks | Three-dimension methodology — see [`docs/evaluation-methodology.md`](docs/evaluation-methodology.md) |

**Architecture:**
```
Telegram Trigger ─┐
                   ├──► Agent ──► IF (interface routing) ──► Send response → Decision Logger (approval)
n8n Chat Trigger ─┘                                      └──► Rejection Detector ──► Decision Logger (rejection)
```

**Key technical constraint:** the calendar trigger used operates in polling-only mode (no webhook) in this environment — deactivating/reactivating the workflow triggers a full history backfill, and each sub-calendar requires its own dedicated trigger using list-based (not ID-based) selection to maintain polling state correctly. A non-obvious constraint that caused early instability before it was diagnosed.

---

## System Prompt Architecture — MIND Framework

* **Mission:** Single-sentence scope — calendar management and time protection across three accounts. Not a general assistant.
* **Intelligence Rules (12):** Priority order (client deliverables > relationship time > gym > deep work > job search > admin > community project), protected time blocks (preferred gym window, sleep buffer), conflict checking across all accounts before proposing, and a rejection-marker protocol.
* **Navigation Rules:** Always name the specific sub-calendar in a proposal, never create an event without explicit confirmation, offer no more than two alternatives unless asked, and the rejection marker — when present — must be the absolute last line of the response.
* **Data Contract:** The user message is dynamic input only (the current message text); all behavioral rules live in the system message, not the per-turn prompt.

---

## 📊 Known Issues (Flagged, Not Hidden)

Three real issues surfaced during use and are documented for the next refinement pass rather than smoothed over:

1. **Rejection marker leaking into user-facing output** — the structured `[DECISION: ...]` tag was visible in the Telegram response. Fix identified: strip everything from the marker onward before sending, in a dedicated node between the agent and the send step.
2. **Greeting messages logging as approved decisions** — a "hello" was being captured as an approval event. Fix identified: filter logger nodes to skip rows where the proposal is just a greeting.
3. **Event type over-defaulting to "general"** — the keyword-based classifier wasn't catching enough categories. Fix identified: expand the keyword list feeding the classification.

---

## Evaluation Architecture

Evaluation is split across three dimensions — decision quality (behavioral, longitudinal), rule adherence (structural, real-time), and Phase 2 readiness (upcoming). See [`docs/evaluation-methodology.md`](docs/evaluation-methodology.md) for the full breakdown.

---

## 🚀 Roadmap

| Workflow | Status | Description |
|---|---|---|
| **WF1 — Chat Interface** | ✅ Live | Dual-trigger agent, 10 calendar tools, decision logging — this spec |
| **WF2 — Calendar Watch** | In Progress | Per-sub-calendar trigger monitoring with deduplication |
| **WF3 — Scheduled Audit/Scan** | Upcoming | Recurring schedule audit and forward-looking scan |
| **WF4 — Eval Harness** | Upcoming | LLM-as-a-judge evaluation against the accumulated decision log — Phase 2 readiness validation |

---

## 🎥 Demo

> *Demo link — coming soon.*
