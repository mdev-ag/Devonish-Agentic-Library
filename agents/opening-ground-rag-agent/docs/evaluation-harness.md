# Evaluation Harness — Opening Ground RAG Agent

**Status: does not exist yet.** This document is written differently from the evaluation-harness docs elsewhere in this repository — those describe a live tiered evaluation system; this one documents a confirmed absence and the planned first pass. That distinction matters and isn't smoothed over: verified directly against the workflow export, this build ships with no eval trigger, no test branch, and no automated scoring of any kind.

---

## What's actually missing

* **No classification-accuracy check.** The system prompt routes every incoming message into one of four response types (Research Question, Document Check, Completeness Check, Open Support) before generating a response. Nothing verifies this routing is correct — a message intended as a document check could silently be answered as a research question with no signal that it happened.
* **No citation-faithfulness scoring.** Every response is required to label claims with a source (📄 knowledge base, 🌐 web, ⚠️ general knowledge, 🚫 not found), but nothing checks whether a claim tagged 📄 is actually supported by the retrieved chunk it cites.
* **No fallback-quality comparison.** GPT-4.1 Nano is configured as an automatic fallback for GPT-4.1 Mini, but the two models have never been run side by side on the same inputs to confirm the fallback holds acceptable quality when it takes over.
* **No retrieval-quality check.** Top-K 10 retrieval against the Supabase vector store has not been validated against known question/answer pairs to confirm the right chunks are actually being surfaced.

---

## Why this happened

This build was shipped fast, first as a personal tool for a specific and narrow use case (speeding up strategy work with one colleague), then handed off once the value was clear. The evaluation discipline applied to the client-delivery builds elsewhere in this portfolio (Inari's tiered binary-gate/LLM-judge/APF structure, Nico's extraction-fidelity/conversation-fidelity split) was built in from day one on those projects because they were scoped as production client deliverables from the start. This one wasn't — it grew into a standalone tool after the fact, and evaluation infrastructure wasn't retrofitted once the scope changed. That's a real process gap, not a technical limitation — the vector store and agent architecture here support the same eval patterns used elsewhere without any redesign.

---

## Planned first pass (not yet built)

| Tier | Eval | What it would check | Method |
|---|---|---|---|
| 1 — Binary gate | Classification accuracy | Does a labeled set of 15–20 real message examples (across all four types) route to the correct response format? | Hand-labeled test set, run against the live agent, pass/fail per message |
| 1 — Binary gate | Source-label presence | Does every factual claim in a sampled response carry exactly one of the four required labels? | Regex/structural check over response text |
| 2 — LLM-as-judge | Citation faithfulness | For claims labeled 📄, does the cited source actually support the claim? | A second LLM call compares the claim against the retrieved chunk it cites; scored 1–5 |
| 2 — LLM-as-judge | Fallback parity | Does GPT-4.1 Nano's output, on the same input, stay within an acceptable quality band of GPT-4.1 Mini's? | Run the same test set through both models; score both with the same judge rubric; compare |

This mirrors the tiered structure used on the other builds in this repository deliberately — the intent is to bring this project up to the same evaluation standard, not invent a separate methodology for it.

---

## Why this is documented this way

Every other project in this portfolio leads with "evaluation as infrastructure, built alongside the agent, not bolted on after." This one is the exception, and hiding that would undercut the credibility of the claim everywhere else it's made. Naming the gap plainly, with a concrete plan to close it, is the more defensible position than omitting this document or padding it with eval language that implies more rigor than currently exists.
