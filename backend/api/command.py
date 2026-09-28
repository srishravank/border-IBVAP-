import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body

from backend.models.command import (
    DashboardSummaryResponse,
    SectorRiskSummary,
    RecommendedCameraResponse,
    OperatorActionRequest,
    OperatorActionResponse,
    IncidentNoteRequest,
    IncidentNoteResponse,
    IncidentLifecycleResponse,
    IncidentNarrativeResponse,
    CommandAlertResponse
)
from backend.services.command_service import command_service

logger = logging.getLogger("ibvap.api.command")

router = APIRouter(tags=["Command & Response Center (Phase 6)"])


@router.get("/api/dashboard/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary():
    """Returns top-level operational dashboard summary and sector risk health."""
    return command_service.get_dashboard_summary()


@router.get("/api/sectors/risk", response_model=List[SectorRiskSummary])
def get_sector_risks():
    """Returns sector-by-sector risk distribution and camera operational health."""
    return command_service.get_sector_risks()


@router.get("/api/alerts", response_model=List[CommandAlertResponse])
def get_command_alerts():
    """Returns real-time actionable alerts for human security operators."""
    return command_service.get_alerts()


@router.get("/api/incidents/{incident_id}/recommended-cameras", response_model=List[RecommendedCameraResponse])
def get_recommended_cameras(incident_id: str):
    """Returns explainable recommended forward/nearby tracking cameras for an incident."""
    recs = command_service.get_recommended_cameras(incident_id)
    return recs


@router.get("/api/incidents/{incident_id}/narrative", response_model=IncidentNarrativeResponse)
def get_incident_narrative(incident_id: str):
    """Returns a machine-generated objective narrative using neutral terminology."""
    narrative = command_service.get_incident_narrative(incident_id)
    if not narrative:
        raise HTTPException(status_code=404, detail=f"Narrative for incident '{incident_id}' not found.")
    return narrative


@router.get("/api/incidents/{incident_id}/lifecycle", response_model=IncidentLifecycleResponse)
def get_incident_lifecycle(incident_id: str):
    """Returns the 7-stage lifecycle status and transition history of an incident."""
    lifecycle = command_service.get_incident_lifecycle(incident_id)
    if not lifecycle:
        raise HTTPException(status_code=404, detail=f"Lifecycle for incident '{incident_id}' not found.")
    return lifecycle


@router.post("/api/incidents/{incident_id}/acknowledge", response_model=IncidentLifecycleResponse)
def acknowledge_incident(
    incident_id: str,
    payload: Optional[OperatorActionRequest] = None
):
    """Transitions incident status from ASSESSED/ACTIVE to ACKNOWLEDGED."""
    req = payload or OperatorActionRequest(action="ACKNOWLEDGE")
    success, msg, lifecycle = command_service.transition_incident_status(
        incident_id=incident_id,
        target_status="ACKNOWLEDGED",
        operator_id=req.operator_id,
        role=req.role,
        notes=req.notes or "Incident acknowledged by operator"
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return lifecycle


@router.post("/api/incidents/{incident_id}/investigate", response_model=IncidentLifecycleResponse)
def start_investigation(
    incident_id: str,
    payload: Optional[OperatorActionRequest] = None
):
    """Transitions incident status from ACKNOWLEDGED to INVESTIGATING."""
    req = payload or OperatorActionRequest(action="INVESTIGATE")
    success, msg, lifecycle = command_service.transition_incident_status(
        incident_id=incident_id,
        target_status="INVESTIGATING",
        operator_id=req.operator_id,
        role=req.role,
        notes=req.notes or "Operator started detailed investigation"
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return lifecycle


@router.post("/api/incidents/{incident_id}/close", response_model=IncidentLifecycleResponse)
def close_incident(
    incident_id: str,
    payload: Optional[OperatorActionRequest] = None
):
    """Transitions incident status from INVESTIGATING/ACKNOWLEDGED to CLOSED."""
    req = payload or OperatorActionRequest(action="CLOSE")
    success, msg, lifecycle = command_service.transition_incident_status(
        incident_id=incident_id,
        target_status="CLOSED",
        operator_id=req.operator_id,
        role=req.role,
        notes=req.notes or "Incident investigation concluded and closed"
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return lifecycle


@router.get("/api/incidents/{incident_id}/notes", response_model=List[IncidentNoteResponse])
def get_incident_notes(incident_id: str):
    """Returns all operator notes for an incident."""
    return command_service.get_incident_notes(incident_id)


@router.post("/api/incidents/{incident_id}/notes", response_model=IncidentNoteResponse)
def add_incident_note(
    incident_id: str,
    payload: IncidentNoteRequest
):
    """Appends an operator investigation note without modifying AI risk factors."""
    note_resp = command_service.add_incident_note(
        incident_id=incident_id,
        operator_id=payload.operator_id,
        role=payload.role,
        note_text=payload.note
    )
    if not note_resp:
        raise HTTPException(status_code=400, detail="Note text cannot be empty or incident not found.")
    return note_resp


@router.get("/api/incidents/{incident_id}/actions", response_model=List[OperatorActionResponse])
def get_operator_actions(incident_id: str):
    """Returns the complete audit trail of operator actions for an incident."""
    return command_service.get_operator_actions(incident_id)


@router.post("/api/incidents/{incident_id}/action", response_model=OperatorActionResponse)
def log_operator_action(
    incident_id: str,
    payload: OperatorActionRequest
):
    """Logs an operator action (e.g. FOCUS_CAMERA, BOOKMARK) for the Phase 6/7 audit trail."""
    return command_service.log_operator_action(
        incident_id=incident_id,
        operator_id=payload.operator_id,
        role=payload.role,
        action_name=payload.action,
        notes=payload.notes or "",
        metadata=payload.metadata or {}
    )
