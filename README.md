# Devonish Agentic Library

A curated portfolio of production-grade AI agents built by **Devonish Agentic AI Labs**. Each agent is designed with a Product-first mindset — every build includes a full mission brief, edge case handling, guardrails, and a deployment-ready workflow.

---

## Agents

| Agent | Category | Stack | Status |
|---|---|---|---|
| [Personal Trainer Voice Agent](agents/personal-trainer-voice-agent/README.md) | Voice / Automation | n8n · Retell AI · GPT-4o-mini | ✅ Production |
| Risk Analysis Agent | Analysis / Intelligence | *(coming soon)* | 🔧 In Progress |

---

## Repository Structure

```
agents/
└── [agent-name]/
    ├── workflow.json          ← n8n workflow (sanitized, ready to import)
    ├── README.md              ← Mission brief, product strategy, tech stack
    ├── prompts/               ← All LLM system instructions
    └── docs/
        └── setup-guide.md    ← Credential checklist, variable map, cost estimate
configs/                       ← Private credential backups (git-ignored)
```

Each agent folder is self-contained. You can clone a single agent directory and have everything needed to deploy it.

---

## Design Principles

- **Product-First Documentation** — Every agent ships with a mission brief that articulates the problem, the ROI, and the edge cases handled — not just a list of features.
- **Zero Hardcoded Secrets** — All workflow JSONs use `{{PLACEHOLDER}}` tags. Credentials live in n8n's encrypted store.
- **Prompt Transparency** — System instructions are extracted and versioned in `/prompts` alongside the workflow, not buried inside a JSON blob.
- **Structured Output Contracts** — All LLM nodes enforce `json_schema` with `additionalProperties: false`. No hallucinated keys reach downstream systems.

---

*Built by Devonish Agentic AI Labs · Montreal*
