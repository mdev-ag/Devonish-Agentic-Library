# Setup Guide — Opening Ground RAG Agent

This guide walks you through importing, configuring, and running this agent in your own n8n environment.

---

## 1. Import Instructions

1. Log in to your n8n instance (Cloud or self-hosted).
2. **Workflows** → **+** → **Import from File**.
3. Upload `workflow.json` from this directory.
4. The workflow imports inactive — do not activate until credentials and variables below are configured.
5. This workflow contains two independent trigger nodes (Form Trigger for ingestion, Chat Trigger for the assistant) sharing one Supabase table — both need to be active for the agent to be useful, since the chat flow has nothing to retrieve until at least one document has been ingested.

---

## 2. Credential Checklist

| Credential | n8n Type | Used In | Where to Get It |
|---|---|---|---|
| **Supabase API** | `supabaseApi` | Both vector store nodes (ingestion insert + chat retrieval) | Supabase project settings → API → `service_role` key and project URL |
| **OpenAI API Key** | `openAiApi` | Embeddings (both flows), primary chat model (GPT-4.1 Mini), fallback chat model (GPT-4.1 Nano) | platform.openai.com → API keys |

Both vector store nodes and both embedding nodes must point to the *same* Supabase credential and the *same* `documents` table — the ingestion flow writes to it, the chat flow reads from it as a retrieval tool. Pointing them at different tables silently breaks retrieval with no error.

---

## 3. Database Setup

1. In Supabase, enable the `pgvector` extension on your project.
2. Create a `documents` table using Supabase's standard LangChain vector store schema (`id`, `content`, `metadata`, `embedding`) — the n8n Supabase Vector Store node will create this automatically on first insert if it doesn't already exist, but confirm the embedding dimension matches `text-embedding-ada-002` (1536) if you create it manually.
3. No row-level security policy is configured in the source workflow — if you're deploying this for a real client, add RLS scoped to a service-role-only write/read pattern before going to production, following the same isolation principle used on the Bloc build in this repository.

---

## 4. Variable Map

Replace every `{{PLACEHOLDER}}` in the imported workflow with your own values:

| Placeholder | Where | What to Enter |
|---|---|---|
| `{{SUPABASE_TABLE_NAME}}` | Both vector store nodes | Your Supabase table name (source workflow uses `documents`) |
| `{{AGENT_NAME}}` | Chat Trigger node | Display name shown in the public chat widget |
| `{{AGENT_DESCRIPTION}}` | Chat Trigger node | Short description shown alongside the agent |
| `{{INITIAL_GREETING}}` | Chat Trigger node | The first message shown when a chat session opens |
| `{{SYSTEM_PROMPT_ORG_NAME}}` | AI Agent node — system prompt | The organization name and project scope the assistant should reference — see `prompts/agent-system-prompt.md` for the full text to adapt |

---

## 5. Workflow Architecture Reference

```
FLOW 1 — Ingestion
[Form Trigger: Document Upload (.pdf/.docx/.xlsx)]
      → [Default Data Loader — tags each chunk with source filename]
      → [Embeddings: text-embedding-ada-002]
      → [Supabase Vector Store: insert → documents table]

FLOW 2 — Chat
[Chat Trigger — public widget]
      → [AI Agent]
            ├─ [Window Buffer Memory — short-term context]
            ├─ [Chat Model: GPT-4.1 Mini, temp 0.3 — primary]
            ├─ [Chat Model: GPT-4.1 Nano — automatic fallback]
            └─ [Supabase Vector Store — retrieve-as-tool, top-K 10, reads documents table]
```

---

## 6. Adapting the System Prompt

The AI Agent's system prompt is scoped tightly to one organization and one project (Ethos, for Opening Ground). If reusing this workflow for a different knowledge base:

1. Replace the "WHO YOU ARE" section with your own organization/project description.
2. Keep the four-type classification structure (Research / Document Check / Completeness Check / Open Support) — it's the core design decision of this build, not project-specific boilerplate.
3. Keep the mandatory source-labeling rules (📄 / 🌐 / ⚠️ / 🚫) — these are what make responses auditable regardless of domain.
4. Update the worked example under Type B (the "Ethos Lab" example) to something representative of your own knowledge base, so the model has a concrete pattern to match.

---

*For portfolio or collaboration inquiries, see the top-level repository README.*
