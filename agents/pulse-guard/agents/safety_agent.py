"""
Pulse Guard — Safety Agent Core
Handles protocol lookup, LLM reasoning, and APF observability logging.
"""

import json
import time
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import anthropic

from configs.settings import (
    ANTHROPIC_API_KEY,
    LLM_MODEL,
    LLM_MAX_TOKENS,
    PERF_LOG_PATH,
    PROTOCOLS_PATH,
    SAFETY_PERSONA_PATH,
    HITL_TRIGGER_PRIORITIES,
)

# ---------------------------------------------------------------------------
# Observability — APF Performance Logger
# ---------------------------------------------------------------------------
PERF_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

perf_logger = logging.getLogger("pulse_guard.performance")
perf_logger.setLevel(logging.INFO)

_file_handler = logging.FileHandler(PERF_LOG_PATH)
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ")
)
perf_logger.addHandler(_file_handler)
perf_logger.propagate = False


def _log_span(span_name: str, incident_id: str, duration_ms: float, metadata: Optional[Dict] = None):
    """Record an APF Reasoning Span to the performance audit log."""
    entry = {
        "span": span_name,
        "incident_id": incident_id,
        "duration_ms": round(duration_ms, 2),
        **(metadata or {}),
    }
    perf_logger.info(json.dumps(entry))


# ---------------------------------------------------------------------------
# Protocol Engine
# ---------------------------------------------------------------------------
def _load_protocols() -> dict:
    with open(PROTOCOLS_PATH, "r") as f:
        return json.load(f)


def lookup_protocol(incident_type: str) -> Optional[Dict]:
    """Return the protocol document for a given incident type, or None if unknown."""
    protocols = _load_protocols()
    return protocols.get(incident_type)


# ---------------------------------------------------------------------------
# LLM Reasoning — MIND Framework
# ---------------------------------------------------------------------------
def _load_system_prompt() -> str:
    return SAFETY_PERSONA_PATH.read_text()


def reason_over_incident(
    incident_id: str,
    incident_type: str,
    priority: str,
    description: str,
    location: str,
    protocol: dict,
) -> dict:
    """
    Sends the incident to the LLM with the MIND-framework system prompt.
    Returns the agent's structured response and APF timing metrics.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    system_prompt = _load_system_prompt()

    user_message = f"""
LIVE INCIDENT REPORT
====================
Incident ID    : {incident_id}
Type           : {incident_type}
Priority       : {priority}
Location       : {location}
Description    : {description}

RETRIEVED PROTOCOL
==================
{json.dumps(protocol, indent=2)}

Produce your structured response now. Follow the Navigation output format exactly.
"""

    # --- Reasoning Span: t0 = input received ---
    t0 = time.perf_counter()

    message = client.messages.create(
        model=LLM_MODEL,
        max_tokens=LLM_MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    # --- First Response Latency (FRL) ---
    frl_ms = (time.perf_counter() - t0) * 1000
    agent_response = message.content[0].text

    # --- Reasoning Span: logic branch detection ---
    reasoning_branch = "HITL_GATE" if priority in HITL_TRIGGER_PRIORITIES else "ROUTINE_BROADCAST"
    reasoning_span_ms = (time.perf_counter() - t0) * 1000

    _log_span(
        span_name="first_response_latency",
        incident_id=incident_id,
        duration_ms=frl_ms,
        metadata={"priority": priority, "incident_type": incident_type},
    )
    _log_span(
        span_name="reasoning_span_to_logic_branch",
        incident_id=incident_id,
        duration_ms=reasoning_span_ms,
        metadata={"branch": reasoning_branch, "model": LLM_MODEL},
    )

    return {
        "agent_response": agent_response,
        "reasoning_branch": reasoning_branch,
        "frl_ms": round(frl_ms, 2),
        "reasoning_span_ms": round(reasoning_span_ms, 2),
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
    }
