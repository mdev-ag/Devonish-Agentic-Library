# Setup Guide — Personal Trainer Voice Agent

This guide walks you through importing, configuring, and running the Personal Trainer Voice Agent in your n8n environment.

---

## 1. Import Instructions

### n8n Cloud
1. Log in to your n8n Cloud instance.
2. In the left sidebar, click **Workflows**.
3. Click the **+** button (top right) → select **Import from File**.
4. Upload `agents/Personal Trainer Voice Agent.json`.
5. The workflow will open in the canvas in an **inactive** state — do not activate it until all credentials and variables are configured (Steps 2 & 3 below).

### Self-Hosted / Docker
1. Navigate to your n8n instance URL.
2. Follow the same steps above, or place the JSON in your n8n `workflows` directory and restart the service if using file-based imports.

> **Note:** The workflow is set to `"active": false` by default. It will not trigger automatically until you toggle it on after completing configuration.

---

## 2. Credential Checklist

Create each of the following credentials in n8n under **Settings → Credentials** before activating the workflow. Each credential maps to one node.

| Credential | n8n Type | Used In Node | Where to Get It |
|---|---|---|---|
| **Google Calendar OAuth2** | `googleCalendarOAuth2Api` | `Get many events` | [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials |
| **OpenAI API Key** | `openAiApi` | `Message a model` (×2) | [platform.openai.com](https://platform.openai.com) → API Keys |
| **Retell AI API Key** | `httpHeaderAuth` | `HTTP Request` | Retell AI Dashboard → API Keys. Set as Header: `Authorization: Bearer YOUR_KEY` |
| **Gmail OAuth2** | `gmailOAuth2` | `Send a message` | [Google Cloud Console](https://console.cloud.google.com) → same OAuth app as Calendar (add Gmail scope) |

> **Tip:** The Google Calendar and Gmail credentials can share the same Google OAuth2 app if you enable both the Calendar API and Gmail API scopes in your Google Cloud project.

---

## 3. Variable Map

After importing, replace every `{{PLACEHOLDER}}` tag in the workflow with your actual values. These appear in the node parameters on the canvas.

| Placeholder | Node | What to Enter |
|---|---|---|
| `{{YOUR_GOOGLE_CALENDAR_ID}}` | `Get many events` | Your Google Calendar ID. Find it in Google Calendar → Settings → *[Your Calendar]* → **Calendar ID** (format: `xxxx@group.calendar.google.com` or `yourname@gmail.com`) |
| `{{YOUR_RETELL_FROM_NUMBER}}` | `HTTP Request` | Your Retell AI outbound phone number in E.164 format (e.g., `+14385550100`) |
| `{{YOUR_RETELL_AGENT_ID}}` | `HTTP Request` | Your Retell AI Agent ID. Found in the Retell Dashboard under your agent's settings (format: `agent_xxxxxxxxxxxxxxxx`) |
| `{{YOUR_EMAIL_ADDRESS}}` | `Send a message` | The Gmail address where coaching briefings should be delivered |
| `{{N8N_CREDENTIAL_ID}}` | All credentialed nodes | Auto-populated by n8n when you attach credentials in Step 2 — you do not set this manually |
| `{{N8N_INSTANCE_ID}}` | Workflow metadata | Auto-populated by your n8n instance on first save — you do not set this manually |

> **Note:** `{{N8N_CREDENTIAL_ID}}` and `{{N8N_INSTANCE_ID}}` are internal n8n references. They will be automatically assigned when you link credentials to nodes and save the workflow. You do not need to edit these by hand.

---

## 4. Cost Estimate (Per 100 Runs)

A single "run" of this workflow constitutes one full client cycle: one outbound Retell AI call + one inbound webhook summary + two GPT-4.1-mini LLM calls.

### OpenAI (GPT-4.1-mini)

| Node | Est. Input Tokens | Est. Output Tokens |
|---|---|---|
| `Message a model` (Extraction) | ~600 | ~150 |
| `Message a model1` (Transcript Analysis) | ~1,000 | ~150 |
| **Per Run Total** | **~1,600** | **~300** |

**GPT-4.1-mini pricing:** `$0.40 / 1M input tokens` · `$1.60 / 1M output tokens`

| | Cost |
|---|---|
| Input (1,600 tokens × 100 runs) | ~$0.064 |
| Output (300 tokens × 100 runs) | ~$0.048 |
| **OpenAI subtotal / 100 runs** | **~$0.11** |

### Retell AI (Outbound Call)

Retell AI bills per minute of call time. A typical check-in call runs **1–2 minutes**.

| | Cost |
|---|---|
| Est. cost per call minute | ~$0.07–$0.11 |
| Est. cost per call (1.5 min avg) | ~$0.12 |
| **Retell AI subtotal / 100 runs** | **~$12.00** |

### Total Estimate

| Provider | Cost / 100 Runs |
|---|---|
| OpenAI (GPT-4.1-mini) | ~$0.11 |
| Retell AI (voice calls) | ~$12.00 |
| n8n Cloud | Included in your plan (execution credits) |
| **Total** | **~$12.11** |

> **Disclaimer:** These are estimates based on average token counts and published pricing as of Q2 2026. Actual costs will vary with call duration, transcript length, and provider pricing changes. Verify current Retell AI per-minute rates in your dashboard.

---

## 5. Workflow Architecture Reference

```
[Schedule Trigger]
      │
      ▼
[Google Calendar — Get Events (next 24h)]
      │
      ▼
[GPT-4.1-mini — Extract: name, phone, time, reason]
      │
      ▼
[Edit Fields — Map extracted JSON to workflow vars]
      │
      ▼
[Retell AI — POST /v2/create-phone-call]
      │
      ▼ (async — Retell fires webhook on call end)

[Webhook — Receive Retell call summary]
      │
      ▼
[GPT-4.1-mini — Analyze transcript: energy, injuries, confirmation]
      │
      ▼
[Gmail — Send structured coaching brief]
```

---

*For portfolio or collaboration inquiries, see the project README.*
