# Setup Guide — Cross-Border Freight Coordination Agent

This guide walks you through importing, configuring, and running this agent in your own n8n environment. All identifiers below are generic placeholders — see [`confidentiality-note.md`](confidentiality-note.md) for why.

---

## 1. Import Instructions

1. Log in to your n8n instance (Cloud or self-hosted).
2. **Workflows** → **+** → **Import from File**.
3. Upload `workflow.json` from this directory.
4. The workflow imports inactive — do not activate until credentials and variables below are configured.

---

## 2. Credential Checklist

| Credential | n8n Type | Used In | Where to Get It |
|---|---|---|---|
| **Cloud Storage OAuth2** (Drive-equivalent) | e.g. `googleDriveOAuth2Api` | File ingestion trigger, BOL template copy | Your cloud provider's console |
| **Spreadsheet OAuth2** | e.g. `googleSheetsOAuth2Api` | Staging shipment table read/write | Same OAuth app as above, with Sheets scope enabled |
| **Email OAuth2** | e.g. `gmailOAuth2` | Draft creation, HITL approval emails, alerts | Same OAuth app, with Email scope enabled |
| **LLM API Key** | `openAiApi` (or equivalent) | Extraction agent, drafting agent | Your LLM provider's dashboard |

---

## 3. Variable Map

Replace every `{{PLACEHOLDER}}` in the imported workflow with your own values:

| Placeholder | Where | What to Enter |
|---|---|---|
| `{{SCHEDULE_SOURCE_FOLDER_ID}}` | File ingestion trigger | The cloud storage folder to poll for new shipping schedule files |
| `{{STAGING_SHEET_ID}}` | Spreadsheet nodes | Your staging spreadsheet ID |
| `{{BOL_TEMPLATE_FOLDER_ID}}` | BOL copy node | Folder containing your carrier-specific BOL templates |
| `{{CARRIER_CONFIG}}` | Multiplexer/config node | Array of carrier name/email pairs — this is the single source of truth for carrier routing |
| `{{OPS_CONTACT_EMAIL}}` | Booking window email | Where the carrier-selection request is sent |
| `{{OPERATOR_ALERT_EMAIL}}` | Alert nodes | Where validation-failure alerts are sent |

---

## 4. Workflow Architecture Reference

```
FLOW 1 — Ingestion
[Storage Trigger] → [Dedup Check] → [Download] → [PDF Extract]
      → [GPT-4o mini — Extraction Agent] → [Schema Validation]
      → [Shipment Splitter] → [Append to Staging Sheet]

FLOW 2 — Daily Outreach + BOL
[Schedule Trigger] → [Read Staging Sheet] → [3-Business-Day Filter]
      → [Reference Number Generator] → [Carrier Multiplexer]
      → [GPT-4o mini — Drafting Agent] → [Draft Validation]
      → [Booking Window Email] + [Draft Creation (per carrier)]
      → [Wait — Carrier Selection Webhook] (24hr timeout → escalation)
      → [BOL Template Copy] → [BOL Field Fill] → [Status Update]
```

---

*For portfolio or collaboration inquiries, see the top-level repository README.*
