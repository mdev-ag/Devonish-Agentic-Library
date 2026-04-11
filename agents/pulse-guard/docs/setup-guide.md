# Pulse Guard — Local Setup Guide

## Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)
- `pip` or a virtual environment manager (`venv`, `poetry`, `conda`)

---

## 1. Clone & Navigate

```bash
cd agents/pulse-guard
```

---

## 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in the required values:

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key. Starts with `sk-ant-`. |
| `INTERNAL_API_KEY` | Yes | Shared secret between FastAPI and Streamlit. Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `LLM_MODEL` | No | Default: `claude-sonnet-4-6`. Switch to `claude-opus-4-6` for highest reasoning fidelity. |
| `LLM_MAX_TOKENS` | No | Default: `1024`. Increase to `2048` for verbose protocol outputs. |
| `APP_ENV` | No | `development` or `production`. |
| `API_PORT` | No | Default: `8000`. |
| `API_BASE_URL` | No | Default: `http://localhost:8000`. Update if running on a remote server. |

> **Security Note:** Never commit your `.env` file. It is included in `.gitignore` by default.

---

## 5. Run the FastAPI Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

Interactive API docs: `http://localhost:8000/docs`

---

## 6. Run the Streamlit Frontend

Open a **second terminal** (with the virtual environment activated):

```bash
streamlit run app.py
```

The dashboard will be available at `http://localhost:8501`.

---

## 7. Verify the System

Run the health check:
```bash
curl http://localhost:8000/health
# Expected: {"status":"operational","service":"Pulse Guard"}
```

Submit a test incident via the Streamlit dashboard or directly via the API:
```bash
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_INTERNAL_API_KEY" \
  -d '{
    "incident_type": "Conflict",
    "priority": "Urgent",
    "description": "Two patrons are arguing aggressively near the bar. One has pushed the other.",
    "location": "Main Bar Area",
    "reporter_id": "STAFF-001"
  }'
```

An `Urgent` incident will return `"status": "PENDING_APPROVAL"` — navigate to the Streamlit dashboard to authorize the broadcast.

---

## 8. Performance Audit Log

APF observability metrics (FRL and Reasoning Spans) are written to:

```
docs/performance-audit.log
```

Each entry is a JSON line:
```json
{"span": "first_response_latency", "incident_id": "...", "duration_ms": 1423.5, "priority": "Urgent", "incident_type": "Conflict"}
{"span": "reasoning_span_to_logic_branch", "incident_id": "...", "duration_ms": 1430.1, "branch": "HITL_GATE", "model": "claude-sonnet-4-6"}
```

---

## Directory Structure

```
pulse-guard/
├── main.py                    # FastAPI backend — incident intake & HITL gate
├── app.py                     # Streamlit dashboard
├── requirements.txt
├── .env.example
├── agents/
│   └── safety_agent.py        # LLM reasoning + APF observability
├── prompts/
│   └── safety-persona.md      # MIND Framework system prompt
├── data/
│   └── protocols.json         # Protocol Engine — Medical, Conflict, Fire
├── configs/
│   └── settings.py            # Environment variable management
└── docs/
    ├── setup-guide.md         # This file
    └── performance-audit.log  # Auto-generated APF log
```
