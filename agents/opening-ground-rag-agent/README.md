# Opening Ground — RAG Research & Document-Check Agent

*Built for Opening Ground, a Vancouver-based social impact organization focused on youth programming, social entrepreneurship, and community development, in support of their Ethos Lab project. Opening Ground has given clearance to reference them by name — social impact work is core context here, not anonymized client work. See [`docs/setup-guide.md`](docs/setup-guide.md) for deployment detail.*

## 🎯 The Mission

**What:** A two-flow retrieval-augmented agent that ingests Opening Ground's Ethos project documentation (program frameworks, curriculum materials, grant documents, camp schedules, workshop guides, organizational reports) and answers questions, checks drafts, and surfaces gaps against that knowledge base through a chat interface — with every factual claim source-labeled.

**The Problem:** Opening Ground's internal documentation wasn't tracked or citable, and relevant external research wasn't easy to reference either. Strategy work kept stalling on "did we already look at this?" — not on a lack of information, but on a lack of a way to prove the information had already been found and used.

**The Solution:** A knowledge base built once (document upload → vector store) and queried repeatedly through a single chat agent that classifies every incoming message into one of four response types — Research Question, Document Check, Completeness Check, or Open Support — and executes a distinct, structured response format for each, rather than defaulting to generic RAG chat behavior.

**The meta-point:** Built first as a personal tool to speed up my own strategy work with a colleague, then handed off as a client-owned standalone once it was clear Opening Ground's own team needed the same cross-referencing capability after the engagement ended. The value was never the research output itself — it was making prior work provably citable before starting new work.

---

## 🧠 Product Strategy & Architecture Decisions

* **Four-type response classification, not generic RAG chat:** The system prompt forces the agent to classify every message before responding — Research Question, Document Check, Completeness Check, or Open Support — and execute only that response format. This exists specifically because the highest-value use case (checking a draft against the knowledge base) has a different shape than answering a question, and a generic RAG agent tends to collapse both into a knowledge-base summary. The prompt calls this out explicitly: *"If the message contains a block of text the user has written — it is a document check. Do not summarize the knowledge base."*

* **Document Check as a fixed four-part structure, not free text:** ✅ Aligned / ⚠️ Missing / ❌ Gaps / 💡 Suggestions, each with a required source citation. This is the single most opinionated design decision in the build — it trades conversational flexibility for a repeatable, scannable output the team can act on directly, and it's enforced with a hard rule in the prompt ("Never replace this structure with a knowledge base summary") rather than left to model judgment.

* **Mandatory source-labeling on every claim:** Four label types (📄 from knowledge base, 🌐 from web search, ⚠️ general knowledge — unverified, 🚫 not in the knowledge base) that must appear on every factual statement, with an explicit rule against mixing sources in one statement without labeling each one. This is a Glass Box decision — it makes it possible to tell, at a glance, what the agent is confident about versus what it's guessing at.

* **Primary/fallback model pairing:** GPT-4.1 Mini (temperature 0.3) as the primary reasoning model, with GPT-4.1 Nano configured as an automatic fallback (`needsFallback: true`) if the primary is unavailable. This is the only build in the portfolio using n8n's native model-fallback mechanism rather than a single fixed model — a deliberate availability decision for a tool a small team depends on daily, though it comes with an open question flagged below: the fallback's output quality has never been directly compared against the primary's.

* **Decoupled ingestion and retrieval flows:** Document upload (Flow 1) and chat (Flow 2) are entirely separate triggers writing to and reading from the same Supabase `documents` table. New documents can be added at any time without touching or redeploying the chat flow — the two concerns don't share a deploy surface.

---

## 🛠️ Technical Stack

| Layer | Technology | Role |
|---|---|---|
| **Orchestration** | n8n Cloud | Two decoupled flows: document ingestion and chat |
| **Vector store** | Supabase (`documents` table) | Shared store — written by ingestion, read by chat as a retrieval tool |
| **Embeddings** | OpenAI `text-embedding-ada-002` | Used identically on both the ingestion and retrieval sides |
| **Chat model — primary** | GPT-4.1 Mini (temperature 0.3) | Main reasoning model for the AI Agent node |
| **Chat model — fallback** | GPT-4.1 Nano | Automatic fallback (`needsFallback`) if the primary is unavailable — quality parity vs. primary not yet evaluated |
| **Memory** | Window Buffer Memory (n8n LangChain node) | Short-term conversational context within a chat session |
| **Retrieval** | Supabase Vector Store, `retrieve-as-tool` mode, top-K 10 | Exposed to the AI Agent as a callable tool, not a pre-fetch step |
| **Document ingestion** | n8n Form Trigger (PDF / DOCX / XLSX) → Default Data Loader → Supabase Vector Store (insert) | Source filename captured as retrieval metadata on every chunk |
| **Interface** | n8n native chat widget (public) | Public-facing chat trigger, embeddable for the Opening Ground team |
| **Evaluation & Testing** | None — confirmed absent, see [`docs/evaluation-harness.md`](docs/evaluation-harness.md) | Flagged honestly rather than omitted |

**Architecture:**
```
FLOW 1 — Ingestion
[Form Trigger: Document Upload] → [Default Data Loader — source metadata]
      → [Embeddings: text-embedding-ada-002] → [Supabase Vector Store: insert → documents]

FLOW 2 — Chat
[Chat Trigger] → [AI Agent]
      ├─ [Window Buffer Memory]
      ├─ [Chat Model: GPT-4.1 Mini, temp 0.3 (primary)]
      ├─ [Chat Model: GPT-4.1 Nano (fallback)]
      └─ [Supabase Vector Store — retrieve-as-tool, top-K 10 ← documents]
```

---

## 📊 Known Issues (Flagged, Not Hidden)

Two real gaps, surfaced here rather than smoothed over:

1. **No evaluation harness exists.** Confirmed directly against the workflow export — no eval trigger, no test branch, nothing scoring whether a message actually gets classified into the correct response type, nothing checking citation faithfulness against retrieved chunks, and no comparison of the GPT-4.1 Nano fallback's output quality against the GPT-4.1 Mini primary. This is the one build in the portfolio that doesn't yet practice "evaluation as infrastructure" — see [`docs/evaluation-harness.md`](docs/evaluation-harness.md) for the planned first pass rather than a retrofit dressed up as complete.
2. **No baseline metric captured before handoff.** The adoption story (the client team kept using the tool after the engagement ended) is real, but no time-saved-per-research-cycle number was captured beforehand, so the outcome is qualitative only, not yet quantified.

---

## 🚀 Roadmap

| Item | Status | Description |
|---|---|---|
| **Ingestion + Chat (this spec)** | ✅ Live | Two-flow RAG pipeline, four-type response classification, mandatory source labeling |
| **Evaluation harness** | Not started | Classification-accuracy test set + citation-faithfulness scoring + fallback-model quality comparison — see [`docs/evaluation-harness.md`](docs/evaluation-harness.md) |
| **Adoption baseline** | Not started | Retroactive time-saved-per-research-cycle measurement with the Opening Ground team |

---

## 🎥 Demo

> *Demo link — coming soon.*

---

## 🚀 Deployment & Scalability

1. **Import:** Load `workflow.json` from this directory into your n8n instance.
2. **Configuration:** Replace all `{{PLACEHOLDER}}` credential identifiers with your own — see [`docs/setup-guide.md`](docs/setup-guide.md).
3. **Credentials Required:** Supabase project (URL + service key), OpenAI API key.
4. **Environment:** Built and running on n8n Cloud; compatible with self-hosted n8n.
5. **Scalability path:** The knowledge base grows purely by document upload through Flow 1 — no workflow changes required to add content. Scaling to a second client project would mean a second Supabase table + a second chat trigger scoped to it, not a rewrite of the classification logic in the system prompt.
