# Evaluation Methodology — Bloc

Evaluation is split across three dimensions, documented explicitly because conflating them is one of the most common errors in agentic eval design — a system can pass a structural check while making genuinely bad decisions, or vice versa.

---

## Dimension 1 — Decision Quality (Behavioral, Longitudinal)

The primary eval signal isn't automated — it's behavioral. Every interaction produces a logged row in the decision-log table. After several weeks, the table reveals:

- Which proposals get approved vs. rejected, by event type
- Which days specific block types get rejected most often
- Whether approval rates differ by trigger source (mobile vs. desktop interface)
- High-frequency rejection reasons that should propagate back into the behavioral rules

This is deliberately not evaluated against a static benchmark. It's evaluated against what actually gets approved — the correct success metric for a personal, preference-driven system, where "correct" is defined by the user's own behavior over time rather than an external rubric.

**Design principle:** success here is "feeling balanced across life domains with tasks executing in priority order" — not maximizing calendar density. Evaluation has to match the actual objective, which is qualitative, not volumetric. A system that books more events isn't succeeding if it's booking the wrong things.

---

## Dimension 2 — Behavioral Rule Adherence (Structural, Real-Time)

This dimension is observable directly from the interaction log without a separate evaluation harness:

- Does every proposal name a specific sub-calendar? (Navigation Rule)
- Does the agent check for conflicts before proposing? (Intelligence Rule)
- Does the agent append the rejection marker correctly on explicit rejections?
- Does the agent require confirmation before creating any event? (HITL Gate)

Failures on these dimensions are caught in real time and fed back as system-prompt refinements — the three known issues documented in the main README (visible rejection marker, greeting logged as approval, over-defaulted event classification) came directly out of this dimension.

---

## Dimension 3 — Phase 2 Readiness (Upcoming)

The logging architecture was built specifically to feed a future evaluation harness that will test a planned memory/reasoning layer: given N weeks of accumulated decision data, do the agent's proposals improve in alignment with observed approval patterns? That evaluation will use LLM-as-a-judge scoring against the historical preference log — the same methodology used elsewhere in this repository's voice agent evaluation harness.

---

## Why Build the Logging Layer Before the Reasoning Layer Exists

A deliberate sequencing decision: the decision-log table was built and started accumulating data from the first day of Workflow 1, well before there's any reasoning layer to consume it. The alternative — building the logging layer at the same time as the reasoning layer — would mean the reasoning layer's first real training data starts from zero on the day it ships. Starting the data accumulation early means Phase 2, whenever it ships, inherits weeks or months of real preference signal instead of starting cold.
