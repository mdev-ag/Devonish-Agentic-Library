# Setup Guide — Bloc (Personal AI Scheduling Agent)

This guide covers importing and configuring this agent in your own n8n environment. All identifiers are generic placeholders — see [`privacy-note.md`](privacy-note.md).

---

## 1. Import Instructions

1. Log in to your n8n instance (Cloud or self-hosted).
2. **Workflows** → **+** → **Import from File**.
3. Upload `workflow.json` from this directory.
4. The workflow imports inactive — configure credentials and variables below before activating.

---

## 2. Credential Checklist

| Credential | n8n Type | Used In | Notes |
|---|---|---|---|
| **Calendar OAuth2 — Account A** | `googleCalendarOAuth2Api` | Read/create nodes for your primary account | One credential covers all sub-calendars within an account |
| **Calendar OAuth2 — Account B** | `googleCalendarOAuth2Api` | Business/work account calendar nodes | |
| **Calendar OAuth2 — Account C** | `googleCalendarOAuth2Api` | Third account calendar nodes | Only needed if you're managing 3 accounts like the original build; reduce tool count if you have fewer |
| **Anthropic API Key** | `anthropicApi` | Agent node LLM calls | |
| **Database service role key** | Your chosen backend (e.g. Supabase) | Decision logger nodes | Use a service-role/write-scoped key, never a public/anon key, for write operations |

---

## 3. Variable Map

| Placeholder | Where | What to Enter |
|---|---|---|
| `{{ACCOUNT_A_CALENDAR_IDS}}` | Read/create nodes | Your primary account's calendar and sub-calendar IDs |
| `{{ACCOUNT_B_CALENDAR_IDS}}` | Read/create nodes | Second account's calendar IDs |
| `{{ACCOUNT_C_CALENDAR_IDS}}` | Read/create nodes | Third account's calendar IDs (if applicable) |
| `{{DECISION_LOG_TABLE}}` | Logger nodes | Your decision-log table name |
| `{{PRIORITY_RULES}}` | Agent system message | Your own priority order and protected time blocks — this is the part you should genuinely rewrite for your own life, not copy verbatim |

---

## 4. Database Schema — Decision Log

| Column | Type | Purpose |
|---|---|---|
| `id` | uuid | Primary key |
| `created_at` | timestamptz | Auto-generated timestamp |
| `week_number` | integer | Enables pattern detection by week |
| `day_of_week` | text | Enables pattern detection by day |
| `event_type` | text | Keyword-classified category |
| `proposed_title` | text | Human-readable label (first ~200 chars of agent output) |
| `proposed_start_time` / `proposed_end_time` / `proposed_calendar` / `proposed_sub_calendar` | text | Reserved for a future structured-proposal phase (currently null) |
| `decision` | text (check constraint) | `approved` \| `rejected` \| `modified` |
| `override_reason` | text | Parsed from the rejection marker |
| `trigger_source` | text (check constraint) | `telegram` \| `chat` |
| `raw_proposal` | text | Full agent output — complete preservation of what was proposed |

---

## 5. Workflow Architecture Reference

```
[Telegram Trigger] ─┐
                     ├─► [Agent] ─► [IF: interface routing]
[Chat Trigger] ──────┘                  ├─► TRUE  → [Send response] → [Decision Logger — Approval]
                                         └─► FALSE → [Decision Logger — Approval]
                     [Agent output] ─► [Rejection Detector: contains "DECISION: rejected"?]
                                         └─► TRUE → [Decision Logger — Rejection] (terminates, does not log as approval)
```

---

*For portfolio or collaboration inquiries, see the top-level repository README.*
