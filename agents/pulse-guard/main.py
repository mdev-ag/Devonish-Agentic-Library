"""
Pulse Guard — FastAPI Backend
Incident intake, HITL gate management, protocol engine, and broadcast pipeline.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents.safety_agent import lookup_protocol, reason_over_incident
from configs.settings import HITL_TRIGGER_PRIORITIES, INTERNAL_API_KEY

# ---------------------------------------------------------------------------
# App Init
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Pulse Guard API",
    description="Nightlife Safety & Incident Management — Human-in-the-Loop Safety Gate",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit dev origin
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory incident store (replace with a database in production)
# ---------------------------------------------------------------------------
incident_store: Dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class IncidentPriority(str, Enum):
    Routine = "Routine"
    Urgent = "Urgent"
    Safety = "Safety"


class IncidentType(str, Enum):
    Medical = "Medical"
    Conflict = "Conflict"
    Fire = "Fire"


class IncidentStatus(str, Enum):
    PROCESSING = "PROCESSING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    BROADCAST = "BROADCAST"
    REJECTED = "REJECTED"


class IncidentReportRequest(BaseModel):
    incident_type: IncidentType
    priority: IncidentPriority
    description: str = Field(..., min_length=10, max_length=2000)
    location: str = Field(..., min_length=2, max_length=200)
    reporter_id: str = Field(..., description="Staff member ID — never exposed in output")


class IncidentResponse(BaseModel):
    incident_id: str
    status: IncidentStatus
    incident_type: str
    priority: str
    location: str
    created_at: str
    agent_response: Optional[str] = None
    broadcast_message: Optional[str] = None
    reasoning_branch: Optional[str] = None
    frl_ms: Optional[float] = None
    hitl_required: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None


class HITLApprovalRequest(BaseModel):
    approver_id: str = Field(..., description="Staff/manager ID approving the broadcast")
    override_message: Optional[str] = Field(
        None, description="Optional: replace the agent's broadcast script with a custom message"
    )


class HITLRejectionRequest(BaseModel):
    approver_id: str
    rejection_reason: str


# ---------------------------------------------------------------------------
# Auth Dependency
# ---------------------------------------------------------------------------
def _verify_internal_key(x_api_key: Annotated[str, Header()]) -> None:
    if x_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key.")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "operational", "service": "Pulse Guard"}


@app.post("/incidents", response_model=IncidentResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_incident(
    payload: IncidentReportRequest,
    x_api_key: Annotated[str, Header()] = ...,
):
    _verify_internal_key(x_api_key)

    incident_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    # --- Protocol Lookup ---
    protocol = lookup_protocol(payload.incident_type.value)
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No protocol found for incident type: {payload.incident_type.value}",
        )

    # --- LLM Reasoning ---
    agent_result = reason_over_incident(
        incident_id=incident_id,
        incident_type=payload.incident_type.value,
        priority=payload.priority.value,
        description=payload.description,
        location=payload.location,
        protocol=protocol,
    )

    # --- HITL Gate Logic ---
    hitl_required = payload.priority.value in HITL_TRIGGER_PRIORITIES
    incident_status = IncidentStatus.PENDING_APPROVAL if hitl_required else IncidentStatus.APPROVED

    # Store the full record (reporter_id is kept internally, never returned)
    incident_store[incident_id] = {
        "incident_id": incident_id,
        "status": incident_status,
        "incident_type": payload.incident_type.value,
        "priority": payload.priority.value,
        "description": payload.description,
        "location": payload.location,
        "reporter_id": payload.reporter_id,  # stored internally only
        "created_at": created_at,
        "agent_response": agent_result["agent_response"],
        "broadcast_message": None,
        "reasoning_branch": agent_result["reasoning_branch"],
        "frl_ms": agent_result["frl_ms"],
        "hitl_required": hitl_required,
        "approved_by": None,
        "approved_at": None,
    }

    # Auto-broadcast routine incidents
    if not hitl_required:
        incident_store[incident_id]["status"] = IncidentStatus.BROADCAST
        incident_store[incident_id]["broadcast_message"] = protocol["resolution_broadcast"]

    return _sanitize_response(incident_store[incident_id])


@app.get("/incidents", response_model=List[IncidentResponse])
def list_incidents(x_api_key: Annotated[str, Header()] = ...):
    _verify_internal_key(x_api_key)
    return [_sanitize_response(inc) for inc in incident_store.values()]


@app.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str, x_api_key: Annotated[str, Header()] = ...):
    _verify_internal_key(x_api_key)
    incident = incident_store.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return _sanitize_response(incident)


@app.post("/incidents/{incident_id}/approve", response_model=IncidentResponse)
def approve_incident(
    incident_id: str,
    payload: HITLApprovalRequest,
    x_api_key: Annotated[str, Header()] = ...,
):
    _verify_internal_key(x_api_key)
    incident = _get_pending_incident(incident_id)

    protocol = lookup_protocol(incident["incident_type"])
    broadcast_message = payload.override_message or protocol["resolution_broadcast"]

    incident["status"] = IncidentStatus.BROADCAST
    incident["broadcast_message"] = broadcast_message
    incident["approved_by"] = payload.approver_id
    incident["approved_at"] = datetime.now(timezone.utc).isoformat()

    return _sanitize_response(incident)


@app.post("/incidents/{incident_id}/reject", response_model=IncidentResponse)
def reject_incident(
    incident_id: str,
    payload: HITLRejectionRequest,
    x_api_key: Annotated[str, Header()] = ...,
):
    _verify_internal_key(x_api_key)
    incident = _get_pending_incident(incident_id)

    incident["status"] = IncidentStatus.REJECTED
    incident["approved_by"] = payload.approver_id
    incident["approved_at"] = datetime.now(timezone.utc).isoformat()
    incident["broadcast_message"] = f"[REJECTED] {payload.rejection_reason}"

    return _sanitize_response(incident)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_pending_incident(incident_id: str) -> dict:
    incident = incident_store.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")
    if incident["status"] != IncidentStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=409,
            detail=f"Incident is not in PENDING_APPROVAL state. Current state: {incident['status']}",
        )
    return incident


def _sanitize_response(incident: dict) -> IncidentResponse:
    """Strip internal-only fields (reporter_id, raw description) before returning to client."""
    return IncidentResponse(
        incident_id=incident["incident_id"],
        status=incident["status"],
        incident_type=incident["incident_type"],
        priority=incident["priority"],
        location=incident["location"],
        created_at=incident["created_at"],
        agent_response=incident.get("agent_response"),
        broadcast_message=incident.get("broadcast_message"),
        reasoning_branch=incident.get("reasoning_branch"),
        frl_ms=incident.get("frl_ms"),
        hitl_required=incident.get("hitl_required", False),
        approved_by=incident.get("approved_by"),
        approved_at=incident.get("approved_at"),
    )
