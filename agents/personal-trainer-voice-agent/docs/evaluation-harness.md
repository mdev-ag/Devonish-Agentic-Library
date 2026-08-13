# Evaluation Harness — Personal Trainer Voice Agent

This agent ships with a two-layer evaluation methodology, built after initial production deployment revealed gaps a single testing layer couldn't catch. Both layers are native to the platforms already in the stack — no separate eval framework was introduced.

---

## Why Two Layers

A voice agent has two independent points of failure: it can *misread* what happened on a call (extraction), or it can *mishandle* the call itself while it's happening (conversation). Testing only one gives false confidence about the other — a summarizer that reads transcripts perfectly says nothing about whether the live agent handled a hedged "yes" correctly, and a live agent that behaves well on a scripted persona says nothing about whether its structured output downstream is trustworthy.

| Layer | Tests | Tool | Scope |
|---|---|---|---|
| **1 — Extraction Fidelity** | Does the post-call summarizer correctly read a transcript into structured data? | n8n native Evaluations (Evaluation Trigger → Check If Evaluating → Set Outputs) | 24 hand-written mock transcripts |
| **2 — Conversation Fidelity** | Does the *live* agent handle a real conversation correctly? | Retell AI Simulation Testing (persona-based) | 18 persona test cases |

---

## Layer 1 — Extraction Fidelity (n8n)

Production Retell calls and synthetic test-dataset rows are routed through the **identical** extraction logic (`Message a model1`), then split on an `Evaluation` node (`checkIfEvaluating`):

```
Webhook (production, from Retell)
When fetching a dataset row (Evaluation Trigger, test path)
        ↓ (both feed into)
Message a model1 (GPT-4.1 Mini — extracts structured data from transcript)
        ↓
Evaluation node (checkIfEvaluating)
   ┌────┴────┐
"Normal"   "Evaluation"
   ↓            ↓
Gmail        Evaluation1 (setOutputs)
notification → writes actual_output back to eval dataset
```

This guarantees zero drift between what's tested and what runs in production, and zero risk of a test case triggering a real client notification.

**Test dataset (`nico_transcript_eval`, n8n Data Table):** 24 mock transcripts spanning English, Quebec French, France French, and a deliberate mid-call code-switch case, across: happy-path energy tiers, the mandatory-confirmation guardrail, cancellation, no-answer/third-party-answer scenarios, out-of-scope requests (guarantees, emergencies, program changes), and language fallback.

**A key discipline:** manual review of extraction output happens *before* any automated scoring. Running all 24 tests green on the first pass gave a false sense of completeness — it only proved the summarizer could read a transcript correctly, not that the live agent behaved correctly on a real call. That gap is what Layer 2 exists to close.

### Data Contract (extraction schema)

| Field | Type | Notes |
|---|---|---|
| `client_name` | string | |
| `appointment_confirmed` | `true` / `false` / `null` | Tri-state. `null` = "Not Reached" — added after no-answer calls were forced into a binary and returned inconsistent results. |
| `cancellation_reason` | string | Added after cancellation reasons were found bleeding into `health_injury_notes`, which had no defined boundary. |
| `energy_level` | integer 1–10 (0 if N/A) | |
| `contextual_drivers` | string | |
| `health_injury_notes` | string | Health/physical context only — explicitly excludes scheduling/cancellation reasons. |

Downstream email logic uses strict equality checks (`=== true / === false / === null`) rather than truthy ternaries — a bug was caught where `null` (Not Reached) evaluated as falsy and would have mislabeled no-answer calls as "Cancelled."

---

## Layer 2 — Conversation Fidelity (Retell)

Retell's native AI Simulated Chat / Batch Simulation Testing runs 18 persona-based test cases (Identity / Goal / Personality format, with explicit success criteria and dynamic variables) across the same guardrail categories, in English, Quebec French, and France French.

Path B/C scenarios (someone else answers, voicemail) are deliberately **excluded** from simulation — Retell's persona format models the caller and can't represent "a different person picked up the phone." These require manual test calls instead.

Success criteria evolved beyond functional correctness to include tone/empathy checks, after a simulation run caught the agent narrating its own internal reasoning aloud ("Acknowledging: user asked to check schedule") — a failure mode invisible to criteria that only check whether the right data came out.

**Model selection was decided at this layer, not from a cost/latency table.** A side-by-side simulation of GPT-4.1 Mini vs. GPT-5 Nano on the identical guardrail moment showed the cheaper model leaking meta-commentary into spoken dialogue; GPT-4.1 Mini stayed in natural persona voice. That direct behavioral evidence — not benchmark assumption — is why GPT-4.1 Mini shipped.

One batch run: 19 test cases, 12 passed (63%), 7 failed (37%) — each failure was read individually rather than trusted at face value (see below).

---

## Bugs Found, By Failure-Mode Category

Categorizing failures matters because the fix differs by category — treating every red result as "the agent is wrong" produces bad fixes.

**Schema bugs** (the data model was wrong, not the agent):
- `appointment_confirmed` forced binary → broke on no-answer calls → fixed with tri-state (`true` / `false` / `null`)
- `health_injury_notes` absorbing cancellation reasons → fixed with a dedicated `cancellation_reason` field

**Prompt/guardrail bugs** (the agent's instructions had a real gap):
- Mandatory-confirmation guardrail accepted a second hedge ("I think so," "probably") as valid confirmation → fixed: hedged language never counts, even on retry
- Energy check accepted vague ranges ("6 or 7, depends on the day") instead of a single number → fixed with explicit clarification requirement
- Internal logging leaked aloud as "Noted: ..." mid-call → fixed by making the convention internal-only, never narrated
- Medical emergency handling reverted to normal flow, switched language, and left no record → fixed with explicit no-reversion, logging, and language-consistency requirements

**Test-data bugs** (the test itself was flawed, not the system under test):
- A fabricated `appointment_time` variable containing "demain" caused a harmless duplicate "demain" in one French closing line — corrected in the dataset, not the prompt.

**Judge-calibration bugs** (the evaluator was wrong, not the agent):
- One test case (Medium Energy, EN) was marked failed by the automated judge; reading the transcript directly showed the agent had behaved correctly. Automated judges get graded with the same scrutiny as the system under test — not trusted blindly.

---

## Engineering Principles This Harness Demonstrates

- **Extraction fidelity ≠ conversation fidelity** — testing one thoroughly gives false confidence about the other.
- **Manual review before automated scoring, always** — establishes a human-verified baseline to calibrate any automated judge against.
- **Automated judges need calibration too** — a "failed" result isn't automatically the system's fault.
- **Additive-only prompt editing** — every fix preserved existing validated script rather than rewriting around it, minimizing regression risk.
- **Isolate variables during testing** — model swaps and prompt fixes were tested separately so causality could be established.
- **Eval infrastructure is a living artifact** — the harness was expanded specifically because real production call patterns revealed scenarios the original suite never covered.

---

## Open Items

- **Latency reconciliation:** current readings are 1050–1400ms against an earlier-cited sub-900ms figure. The lower figure predates guardrail expansion (a longer system message plausibly added latency) and needs to be re-measured against the live Retell dashboard before reuse in any pitch or portfolio material.
- **Regression check:** one test session displayed the old pre-fix "Acknowledging:" meta-commentary bug. Unclear whether this was a stale cached session or an actual regression — needs a fresh confirmation run.
- **Path B/C coverage:** no-answer and third-party-answer guardrails aren't covered by Retell's simulation testing and still require manual test calls to validate directly.
