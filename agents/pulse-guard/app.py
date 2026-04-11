"""
Pulse Guard — Streamlit Operations Dashboard
Submit incidents, monitor HITL gate status, approve/reject broadcasts.
"""

import os
import time
from typing import Optional

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
INTERNAL_API_KEY = os.environ["INTERNAL_API_KEY"]
HEADERS = {"x-api-key": INTERNAL_API_KEY}

PRIORITY_COLORS = {
    "Routine": "#2ecc71",
    "Urgent": "#f39c12",
    "Safety": "#e74c3c",
}

STATUS_COLORS = {
    "PROCESSING": "#95a5a6",
    "PENDING_APPROVAL": "#f39c12",
    "APPROVED": "#3498db",
    "BROADCAST": "#2ecc71",
    "REJECTED": "#e74c3c",
}

# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Pulse Guard | Operations Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #0f1117; }
    .metric-card {
        background: #1a1d27;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 4px solid;
    }
    .pending-badge {
        background: #f39c12;
        color: black;
        border-radius: 4px;
        padding: 2px 8px;
        font-weight: bold;
        font-size: 0.8em;
    }
    .broadcast-badge {
        background: #2ecc71;
        color: black;
        border-radius: 4px;
        padding: 2px 8px;
        font-weight: bold;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# API Helpers
# ---------------------------------------------------------------------------
def submit_incident(payload: dict) -> Optional[dict]:
    try:
        resp = requests.post(f"{API_BASE}/incidents", json=payload, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        st.error(f"API Error: {e.response.status_code} — {e.response.text}")
        return None
    except requests.ConnectionError:
        st.error("Cannot connect to Pulse Guard API. Is the backend running?")
        return None


def fetch_incidents() -> list[dict]:
    try:
        resp = requests.get(f"{API_BASE}/incidents", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def approve_incident(incident_id: str, approver_id: str, override_message: Optional[str]) -> Optional[dict]:
    payload = {"approver_id": approver_id, "override_message": override_message or None}
    try:
        resp = requests.post(
            f"{API_BASE}/incidents/{incident_id}/approve",
            json=payload,
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        st.error(f"Approval failed: {e.response.text}")
        return None


def reject_incident(incident_id: str, approver_id: str, reason: str) -> Optional[dict]:
    payload = {"approver_id": approver_id, "rejection_reason": reason}
    try:
        resp = requests.post(
            f"{API_BASE}/incidents/{incident_id}/reject",
            json=payload,
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        st.error(f"Rejection failed: {e.response.text}")
        return None


# ---------------------------------------------------------------------------
# Sidebar — Submit New Incident
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/nolan/64/shield.png", width=60)
    st.title("Pulse Guard")
    st.caption("Nightlife Safety Operations Center")
    st.divider()

    st.subheader("Report New Incident")

    with st.form("incident_form", clear_on_submit=True):
        incident_type = st.selectbox("Incident Type", ["Medical", "Conflict", "Fire"])
        priority = st.selectbox("Priority", ["Routine", "Urgent", "Safety"])
        location = st.text_input("Venue Zone / Location", placeholder="e.g., Main Floor, VIP Area, Entrance")
        description = st.text_area(
            "Incident Description",
            placeholder="Briefly describe what is happening...",
            height=120,
        )
        reporter_id = st.text_input("Your Staff ID", placeholder="e.g., STAFF-001")

        submitted = st.form_submit_button("Submit Incident", type="primary", use_container_width=True)

    if submitted:
        if not all([location, description, reporter_id]):
            st.error("All fields are required.")
        else:
            with st.spinner("Pulse Guard is analyzing the incident..."):
                result = submit_incident({
                    "incident_type": incident_type,
                    "priority": priority,
                    "description": description,
                    "location": location,
                    "reporter_id": reporter_id,
                })
            if result:
                status_val = result.get("status", "")
                if status_val == "PENDING_APPROVAL":
                    st.warning(f"HITL Gate Active — Incident #{result['incident_id'][:8]} requires approval.")
                elif status_val == "BROADCAST":
                    st.success(f"Incident resolved and broadcast. FRL: {result.get('frl_ms', 'N/A')} ms")
                else:
                    st.info(f"Incident submitted. Status: {status_val}")
                st.rerun()

    st.divider()
    st.caption("Manager ID for HITL approvals:")
    approver_id_input = st.text_input("Approver ID", value="MGR-001", key="approver_id")


# ---------------------------------------------------------------------------
# Main Dashboard
# ---------------------------------------------------------------------------
st.title("Operations Dashboard")

col_refresh, col_spacer = st.columns([1, 5])
with col_refresh:
    if st.button("Refresh", use_container_width=True):
        st.rerun()

incidents = fetch_incidents()

if not incidents:
    st.info("No incidents reported yet. Use the sidebar to submit the first incident.")
    st.stop()

# --- KPI Row ---
pending = [i for i in incidents if i["status"] == "PENDING_APPROVAL"]
broadcast = [i for i in incidents if i["status"] == "BROADCAST"]
safety_count = [i for i in incidents if i["priority"] == "Safety"]

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Incidents", len(incidents))
kpi2.metric("Pending HITL Approval", len(pending), delta=f"{len(pending)} awaiting" if pending else None)
kpi3.metric("Broadcast", len(broadcast))
kpi4.metric("Safety Priority", len(safety_count))

st.divider()

# --- HITL Queue (prominent) ---
if pending:
    st.subheader("HITL Approval Queue")
    st.warning(f"{len(pending)} incident(s) require manual authorization before broadcast.")

    for inc in pending:
        priority_color = PRIORITY_COLORS.get(inc["priority"], "#aaa")
        with st.container():
            st.markdown(
                f"""<div class="metric-card" style="border-color: {priority_color}">
                <b>{inc['incident_type']}</b> — <span style="color:{priority_color}">{inc['priority']}</span>
                &nbsp;&nbsp;|&nbsp;&nbsp; Zone: {inc['location']}
                &nbsp;&nbsp;|&nbsp;&nbsp; ID: <code>{inc['incident_id'][:8]}</code>
                </div>""",
                unsafe_allow_html=True,
            )

            with st.expander("View Agent Analysis & Approve / Reject"):
                st.markdown("**Agent Protocol Analysis:**")
                st.markdown(inc.get("agent_response", "_No response_"))
                st.divider()

                col_a, col_b = st.columns(2)
                with col_a:
                    override = st.text_area(
                        "Override Broadcast Script (optional)",
                        placeholder="Leave blank to use the agent's recommended script.",
                        key=f"override_{inc['incident_id']}",
                    )
                    if st.button(
                        "Authorize & Broadcast",
                        key=f"approve_{inc['incident_id']}",
                        type="primary",
                        use_container_width=True,
                    ):
                        result = approve_incident(
                            inc["incident_id"],
                            st.session_state.get("approver_id", "MGR-001"),
                            override or None,
                        )
                        if result:
                            st.success(f"Broadcast authorized by {result['approved_by']}.")
                            time.sleep(0.5)
                            st.rerun()

                with col_b:
                    rejection_reason = st.text_input(
                        "Rejection Reason",
                        placeholder="Why is this being rejected?",
                        key=f"reason_{inc['incident_id']}",
                    )
                    if st.button(
                        "Reject",
                        key=f"reject_{inc['incident_id']}",
                        use_container_width=True,
                    ):
                        if not rejection_reason:
                            st.error("A rejection reason is required.")
                        else:
                            result = reject_incident(
                                inc["incident_id"],
                                st.session_state.get("approver_id", "MGR-001"),
                                rejection_reason,
                            )
                            if result:
                                st.warning("Incident rejected.")
                                time.sleep(0.5)
                                st.rerun()

    st.divider()

# --- All Incidents Log ---
st.subheader("Incident Log")

non_pending = [i for i in incidents if i["status"] != "PENDING_APPROVAL"]
if not non_pending:
    st.caption("No resolved incidents yet.")

for inc in reversed(non_pending):
    status_color = STATUS_COLORS.get(inc["status"], "#aaa")
    priority_color = PRIORITY_COLORS.get(inc["priority"], "#aaa")

    with st.expander(
        f"[{inc['status']}] {inc['incident_type']} — {inc['location']} | {inc['created_at'][:19]}"
    ):
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**Priority:** <span style='color:{priority_color}'>{inc['priority']}</span>", unsafe_allow_html=True)
        col2.markdown(f"**Status:** <span style='color:{status_color}'>{inc['status']}</span>", unsafe_allow_html=True)
        col3.markdown(f"**FRL:** `{inc.get('frl_ms', 'N/A')} ms`")

        if inc.get("broadcast_message"):
            st.markdown("**Broadcast Message:**")
            st.info(inc["broadcast_message"])

        if inc.get("agent_response"):
            with st.expander("Full Agent Analysis"):
                st.markdown(inc["agent_response"])

        if inc.get("approved_by"):
            st.caption(f"Actioned by: {inc['approved_by']} at {inc.get('approved_at', 'N/A')[:19]}")
