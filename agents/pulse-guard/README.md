# Pulse Guard

> **Nightlife Safety & Logic Agent** — Real-time incident management with Human-in-the-Loop safety gates, MIND Framework reasoning, and legally-compliant protocol dispatch.

---

## The Mission

Event organizers operate in one of the most high-liability, high-chaos environments in the service industry. A single mismanaged incident — a medical emergency called too late, a conflict that escalated because staff used the wrong words, a fire response that caused a crowd stampede — can result in injury, litigation, and venue closure.

**Pulse Guard** eliminates the gap between "something is happening" and "the right response is in the hands of the right person." It is a safety operations agent designed for live event staff: intake incidents via structured reporting, retrieve verified response protocols, generate calm de-escalating communication scripts with LLM reasoning, and gate every high-priority action behind a human authorization checkpoint before anything is broadcast to patrons.

**This is a system built on the premise that speed and safety are not in conflict — they require each other.**

---

## Product Strategy & "Shielded" Logic

### The Wait/Switch HITL Gate

The most critical design decision in Pulse Guard is the **Human-in-the-Loop approval gate**. Any incident tagged `Urgent` or `Safety` enters a `PENDING_APPROVAL` state the moment the agent finishes reasoning. The agent does not broadcast anything.

This is not a UX choice. It is a liability architecture decision.

The agent's output — regardless of how accurate — represents an AI's interpretation of a live safety event. Broadcasting a patron communication script based solely on AI output without a trained human's authorization creates legal exposure and operational risk. The HITL gate enforces a mandatory 2-step verification:

1. **Agent produces the analysis and draft broadcast script** (sub-2 second FRL target).
2. **A credentialed event manager reviews, optionally overrides, and authorizes** the broadcast.

The authorizing manager's ID and timestamp are recorded in the incident record, creating an immutable audit trail.

**Edge Case Handled:** If the agent receives an unknown incident type, it does not hallucinate a protocol — it returns a structured escalation signal and routes immediately to the Event Director, forcing HITL for all unknown scenarios.

### Tone Guardrail

The MIND Framework system prompt contains a hard **Tone Guardrail**: words like "danger", "threat", "attack", "panic", or "fire" (in non-fire contexts) are explicitly prohibited from patron-facing broadcast scripts. This is grounded in crowd dynamics research — language that signals a specific threat causes directed stampede behavior. The agent is instructed to rewrite any output that contains these triggers before delivery.

### Protocol Engine — No Improvisation

The agent does not generate safety protocols from training data. It retrieves verified, pre-authored protocol documents from `data/protocols.json` and grounds its reasoning in that content. The LLM's role is structured synthesis and communication — not protocol authorship. This is the distinction between a tool that augments trained staff and one that creates false confidence.

### ROI & Business Case

| Metric | Baseline (No System) | With Pulse Guard |
|---|---|---|
| Time to correct protocol in hand | 3–8 minutes (paper/radio) | < 5 seconds (protocol lookup) |
| Human authorization layer | Informal, undocumented | Logged, timestamped, auditable |
| Patron communication consistency | Ad-hoc, staff-dependent | Standardized, legally reviewed scripts |
| Post-incident legal documentation | Manual reconstruction | Auto-generated incident log |
| Staff training dependency for protocols | High | Low — system surfaces correct steps |

For a mid-size venue (500–2,000 capacity), a single liability claim from a mismanaged incident can exceed $500K in legal costs. The documentation and consistency layer Pulse Guard provides is a direct risk mitigation asset.

---

## Technical Stack

| Layer | Technology | Role |
|---|---|---|
| **LLM Reasoning** | `claude-sonnet-4-6` | MIND Framework incident analysis & protocol synthesis |
| **API Framework** | FastAPI + Pydantic v2 | Incident intake, HITL gate, broadcast pipeline |
| **Operations Dashboard** | Streamlit | Real-time incident monitoring & HITL approval UI |
| **Protocol Engine** | JSON + Python | Deterministic protocol lookup — no LLM hallucination on safety steps |
| **Prompt Architecture** | MIND Framework | Mission / Intelligence / Navigation / Data Contract |
| **Observability** | Custom APF Logger | Reasoning Spans + First Response Latency per incident |
| **Auth** | Shared secret via `x-api-key` header | Frontend-to-backend internal auth |
| **Config** | `python-dotenv` | All secrets and PII via environment variables |

### MIND Framework System Prompt

The system prompt (`prompts/safety-persona.md`) follows the four-pillar MIND architecture:

- **Mission** — Defines the agent's identity, operating environment, and non-negotiable directives (no panic language, no PII leakage, no improvised protocols).
- **Intelligence** — Describes available tools (Protocol Engine) and the structured input it will receive at runtime.
- **Navigation** — Mandates the exact output structure: Situation Assessment → Protocol Reference → Immediate Actions → Patron Communication Script → Legal Safeguards → Escalation Status.
- **Data Contract** — Specifies the exact input/output schema, including which fields (like `reporter_id`) must never appear in any output.

---

## Performance & Insights

Pulse Guard implements **APF (Agent Performance Framework)** observability, logging two span types per incident to `docs/performance-audit.log`:

| Span | What It Measures | Target |
|---|---|---|
| `first_response_latency` | Time from incident submission to agent response completion | < 2,000 ms |
| `reasoning_span_to_logic_branch` | Time from input to HITL/Routine branch determination | < 2,100 ms |

Log format (JSONL):
```json
{"span": "first_response_latency", "incident_id": "uuid", "duration_ms": 1423.5, "priority": "Urgent", "incident_type": "Conflict"}
{"span": "reasoning_span_to_logic_branch", "incident_id": "uuid", "duration_ms": 1430.1, "branch": "HITL_GATE", "model": "claude-sonnet-4-6"}
```

Token usage (input + output) is also captured per incident for cost monitoring.

---

## Demo

**Submit a Safety-Priority Incident:**
1. Open the Streamlit dashboard at `http://localhost:8501`
2. Select `Incident Type: Medical`, `Priority: Safety`
3. Enter a description and location, submit
4. Watch the incident enter **PENDING_APPROVAL** state in the HITL Queue
5. Review the agent's full analysis, optionally override the broadcast script
6. Click **Authorize & Broadcast** — the incident transitions to `BROADCAST`

**Routine Incident (no HITL):**
- Select `Priority: Routine` — the incident auto-resolves and broadcasts without requiring approval, demonstrating the conditional gate logic.

---

## Deployment & Scalability

### Local Development

See [docs/setup-guide.md](docs/setup-guide.md) for full local setup instructions.

```bash
# Terminal 1 — Backend
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
streamlit run app.py
```

### Production Considerations

| Concern | Recommendation |
|---|---|
| **Incident Store** | Replace in-memory dict with PostgreSQL + SQLAlchemy. The `incident_store` schema maps directly to a relational model. |
| **Auth** | Upgrade `INTERNAL_API_KEY` to JWT with role-based claims (Staff vs. Manager) for granular HITL authorization. |
| **Multi-Venue** | Add a `venue_id` field to the incident schema. Route protocol lookups to venue-specific protocol sets. |
| **Websockets** | Replace Streamlit polling with FastAPI WebSocket push for real-time HITL queue updates at scale. |
| **LLM Fallback** | Implement a fallback to a cached "worst-case" protocol response if the Anthropic API is unreachable, ensuring the system degrades gracefully. |
| **Deployment** | Containerize with Docker. FastAPI → Cloud Run or ECS. Streamlit → Cloud Run or Streamlit Community Cloud. |
