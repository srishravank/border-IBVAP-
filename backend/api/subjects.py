from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException

from backend.models.subject import (
    SubjectResponse,
    SubjectTrackLinkResponse,
    SubjectJourneyResponse
)
from backend.services.cross_camera_engine import cross_camera_engine
from backend.database.connection import SessionLocal
from backend.database.models import SecurityEventModel

router = APIRouter(prefix="/api/subjects", tags=["Global Cross-Camera Subjects"])


@router.get("", response_model=List[SubjectResponse])
def get_all_subjects():
    """Returns all global cross-camera subjects (e.g. SUBJ-001, VEH-001) with their linked camera tracks."""
    return cross_camera_engine.get_all_subjects()


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject_detail(subject_id: str):
    """Returns detailed cross-camera information for a specific global subject."""
    subj = cross_camera_engine.get_subject_by_id(subject_id)
    if not subj:
        raise HTTPException(status_code=404, detail=f"Subject '{subject_id}' not found")
    return subj


@router.get("/{subject_id}/journey", response_model=SubjectJourneyResponse)
def get_subject_journey(subject_id: str):
    """Returns the chronological multi-camera journey path and triggered events for a subject."""
    journey = cross_camera_engine.get_subject_journey(subject_id)
    if not journey:
        raise HTTPException(status_code=404, detail=f"Journey for subject '{subject_id}' not found")
    return journey


@router.get("/{subject_id}/tracks", response_model=List[SubjectTrackLinkResponse])
def get_subject_tracks(subject_id: str):
    """Returns all camera-local track links associated with a global subject."""
    subj = cross_camera_engine.get_subject_by_id(subject_id)
    if not subj:
        raise HTTPException(status_code=404, detail=f"Subject '{subject_id}' not found")
    return subj.track_links


@router.get("/{subject_id}/events")
def get_subject_events(subject_id: str):
    """Returns all confirmed Phase 3 security events triggered by the subject across cameras."""
    subj = cross_camera_engine.get_subject_by_id(subject_id)
    if not subj:
        raise HTTPException(status_code=404, detail=f"Subject '{subject_id}' not found")

    links = subj.track_links
    track_ids = [l.track_id for l in links]
    cam_ids = [l.camera_id for l in links]

    db = SessionLocal()
    try:
        events = db.query(SecurityEventModel).filter(
            SecurityEventModel.track_id.in_(track_ids),
            SecurityEventModel.camera_id.in_(cam_ids)
        ).order_by(SecurityEventModel.created_at.asc()).all()

        return [
            {
                "event_id": e.event_id,
                "camera_id": e.camera_id,
                "track_id": e.track_id,
                "formatted_track_id": e.formatted_track_id,
                "event_type": e.event_type,
                "zone_name": e.zone_name,
                "status": e.status,
                "confidence": e.confidence,
                "timestamp": e.created_at.isoformat(),
                "description": e.description
            }
            for e in events
        ]
    finally:
        db.close()
