from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.models.security_event import (
    SecurityEventResponse,
    EventAcknowledgeRequest,
    VerificationDetail
)
from backend.services.event_manager import event_manager

router = APIRouter(prefix="/api/events", tags=["Security Events & Verification"])


@router.get("", response_model=List[SecurityEventResponse])
def get_security_events(
    camera_id: Optional[str] = Query(default=None),
    zone_id: Optional[str] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200)
):
    """Retrieves verified security events and candidate incidents with filtering."""
    return event_manager.get_security_events(
        camera_id=camera_id,
        zone_id=zone_id,
        event_type=event_type,
        status=status,
        limit=limit
    )


@router.get("/candidates")
def get_verifying_candidates(camera_id: Optional[str] = Query(default=None)):
    """Returns candidate events currently progressing through multi-frame verification gates."""
    return event_manager.get_active_verifying_candidates(camera_id=camera_id)


@router.get("/{event_id}", response_model=SecurityEventResponse)
def get_security_event_detail(event_id: str):
    """Returns full details, bounding box, trajectory, and verification info for a security event."""
    event = event_manager.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Security event '{event_id}' not found")
    return event


@router.get("/{event_id}/verification", response_model=VerificationDetail)
def get_event_verification_audit(event_id: str):
    """Returns the multi-frame verification audit trail for an incident."""
    event = event_manager.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Security event '{event_id}' not found")
    return event.verification


@router.post("/{event_id}/acknowledge", response_model=SecurityEventResponse)
def acknowledge_security_event(event_id: str, req: Optional[EventAcknowledgeRequest] = None):
    """Allows an operator to acknowledge an active security event."""
    notes = req.operator_notes if req else None
    updated = event_manager.acknowledge_event(event_id, notes)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Security event '{event_id}' not found")
    return updated
