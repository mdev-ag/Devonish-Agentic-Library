# Setup Guide — Resilient Supply Chain Risk Analysis Agent

This guide walks you through importing, configuring, and running the Risk Analysis Agent in your n8n environment.

---

## 1. Import Instructions

### n8n Cloud
1. Log in to your n8n Cloud instance.
2. In the left sidebar, click **Workflows**.
3. Click the **+** button (top right) → select **Import from File**.
4. Upload `workflow.json` from the `agents/risk-analysis-agent/` directory.
5. The workflow will open in an **inactive** state. Do not activate until Steps 2–4 are complete.

### Self-Hosted / Docker
Follow the same steps above, or place the JSON in your n8n workflows directory and restart the service.

> **Note:** The workflow is set to `"active": false` by default.

---

## 2. Google Sheets Database Setup

This agent uses a single Google Sheet as both its trigger and its output database. Create it before configuring credentials.

**Spreadsheet name:** `ResilientSupplyAgentDatabase` (or your preferred name — update the node config to match)

### Required Tabs

**Tab 1: `Test_Alerts`** — Input. The Trigger polls this tab for new rows.

| Column | Type | Description |
|---|---|---|
| `alert_id` | string | Unique alert identifier (e.g., `ALT-001`) |
| `alert_from` | string | `agent_a` (primary stockout) or `agent_c` (backup review) |
| `supplier_id` | string | Supplier identifier |
| `component_id` | string | Component under assessment |
| `city` | string | Supplier city |
| `country` | string | Supplier country |
| `lat` | number | Latitude |
| `lon` | number | Longitude |
| `bounding_box` | string | NASA coordinate string: `West,South,East,North` (e.g., `120.5,14.0,121.5,15.0`) |
| `projected_stockout_date` | date | Operational deadline |
| `shortfall_qty` | number | Volume gap in units |
| `severity` | string | Pre-classified severity (`Low`, `Medium`, `High`) |

**Tab 2: `Risk Analysis Results`** — Output. The agent appends one row per assessed component.

| Column | Description |
|---|---|
| Risk ID | `RSK-{alert_id}` |
| Alert ID | Source alert |
| Supplier ID | Supplier assessed |
| Component ID | Component assessed |
| Risk Score | Weighted score (0.0–10.0) |
| Risk Status | `NOMINAL`, `ELEVATED`, or `CRITICAL` |
| Geo Score | Geographic risk sub-score (1–10) |
| Avail Score | Availability risk sub-score (1–10) |
| Lead Time Score | Lead time risk sub-score (1–10) |
| Subst Score | Substitutability risk sub-score (1–10) |
| Lead Time Delta | Expected delay (e.g., `+5 days`) |
| Detailed Findings | Full evidence and reasoning chain |
| Citations | Source links |
| Historical Pattern | Notes from Vector Store |
| Requires Human Review | Boolean |
| HITL Reason | `High Risk`, `Auto-Approved`, or `Auto-Approved (Backup)` |
| Timestamp | Run timestamp |
| Reviewer Comments | Manual input field for human reviewers |
| Final Approval | `YES` or `Pending` |

---

## 3. Credential Checklist

Create each credential in n8n under **Settings → Credentials** before activating.

| Credential | n8n Type | Used In Node | Where to Get It |
|---|---|---|---|
| **OpenAI API Key** (×2) | `openAiApi` | `OpenAI GPT-4 Model`, `OpenAI Chat Model`, `OpenAI Embeddings` | [platform.openai.com](https://platform.openai.com) → API Keys |
| **Google Sheets OAuth2** | `googleSheetsOAuth2Api` | `Append row in sheet` (write account) | [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials |
| **Google Sheets OAuth2 (read)** | `googleSheetsOAuth2Api` | `Get row(s) from Risk analysis result` | Same as above — can be a second OAuth account or same account |
| **Google Sheets Trigger OAuth2** | `googleSheetsTriggerOAuth2Api` | `Google Sheets Trigger1` | Same Google OAuth app — add Sheets scope |

> **Note:** NewsData.io and NASA FIRMS API keys are embedded directly in the HTTP Request Tool URLs as `{{PLACEHOLDER}}` tags (see Variable Map below). They do not use n8n's credential store.

---

## 4. Variable Map

Replace every `{{PLACEHOLDER}}` in the workflow with your actual values.

| Placeholder | Node | What to Enter |
|---|---|---|
| `{{YOUR_NEWSDATA_API_KEY}}` | `NewsData.io Supply Chain News API` | Your NewsData.io API key. Get it at [newsdata.io](https://newsdata.io) → Dashboard → API Key |
| `{{YOUR_NASA_FIRMS_API_KEY}}` | `NASA FIRMS Fire Data API (Resilient)` | Your NASA FIRMS MAP KEY. Register at [firms.modaps.eosdis.nasa.gov](https://firms.modaps.eosdis.nasa.gov/api/area/) |
| `{{YOUR_GOOGLE_SHEET_ID}}` | `Append row in sheet`, `Get row(s) from Risk analysis result`, `Google Sheets Trigger1` | The ID from your Google Sheet URL: `docs.google.com/spreadsheets/d/`**`THIS_PART`**`/edit` |
| `{{YOUR_GOOGLE_SHEET_URL}}` | Same nodes as above | The full Google Sheet URL (auto-populated by n8n once you set the Sheet ID) |
| `{{N8N_CREDENTIAL_ID}}` | All credentialed nodes | Auto-populated by n8n when you attach credentials — do not set manually |

---

## 5. Cost Estimate (Per 100 Runs)

A single "run" = one alert processed through the full pipeline (Scout Agent + all tools + output to Sheets).

### OpenAI (GPT-4o-mini)

| Component | Est. Input Tokens | Est. Output Tokens |
|---|---|---|
| Scout Agent system prompt | ~2,500 | — |
| Tool results (4 sensors) | ~1,500 | — |
| Agent reasoning + output | — | ~800 |
| Embeddings (Vector Store) | ~200 | — |
| **Per Run Total** | **~4,200** | **~800** |

**GPT-4o-mini pricing:** `$0.40 / 1M input` · `$1.60 / 1M output`

| | Cost |
|---|---|
| Input (4,200 × 100 runs) | ~$0.17 |
| Output (800 × 100 runs) | ~$0.13 |
| **OpenAI subtotal / 100 runs** | **~$0.30** |

### External APIs

| API | Cost Model | Est. / 100 Runs |
|---|---|---|
| Open-Meteo | Free (no key) | $0.00 |
| NASA FIRMS | Free (MAP KEY) | $0.00 |
| GDELT | Free (public API) | $0.00 |
| NewsData.io | Free tier: 200 calls/day | $0.00 (within free tier) |
| Google Sheets API | Free (within quota) | $0.00 |

### Total Estimate

| Provider | Cost / 100 Runs |
|---|---|
| OpenAI (GPT-4o-mini + Embeddings) | ~$0.30 |
| All external data APIs | ~$0.00 |
| n8n Cloud | Included in your plan |
| **Total** | **~$0.30** |

> **Note:** NewsData.io free tier caps at 200 requests/day. At 4 calls/alert, you can process ~50 alerts/day on the free tier. Upgrade to a paid plan for higher volume.

---

## 6. Workflow Architecture Reference

```
[Google Sheets Trigger — Test_Alerts tab (weekly poll, rowAdded)]
      │
      ▼
[Loop Over Items — processes alerts one at a time]
      │
      ▼
[Resilient Supply Scout Agent]
      ├── OpenAI GPT-4o-mini (LLM)
      ├── Session Memory (keyed by alert_id)
      ├── Open-Meteo Weather API (tool)
      ├── NewsData.io News API (tool)
      ├── GDELT Geopolitical API (tool)
      ├── NASA FIRMS Fire API (tool)
      ├── Historical Risk Profiles Vector Store (tool)
      └── Risk Calculation Tool (MANDATORY — weighted formula)
      │
      ▼
[Risk Assessment JSON Output Parser — schema enforcement]
      │
      ▼
[Check if Risk Score >= 7 AND alert_from != agent_c]
      │
      ├── TRUE → [Add HITL Flag] → [Split Out] → [Append to Google Sheets]
      │
      └── FALSE → [Mark Auto-Approved] → [Split Out] → [Append to Google Sheets]

─── Separate API Flow ───────────────────────────────────────────
[Webhook GET /risk-analysis-results]
      │
      ▼
[Get rows from Risk Analysis Results tab]
      │
      ▼
[Suppress row_number field]
      │
      ▼
[Respond to Webhook — JSON array]
```
