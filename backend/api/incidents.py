from typing import List, Optional
from fastapi import APIRouter, HTTPException

from backend.models.subject import (
    IncidentResponse,
    IncidentTimelineEntry,
    MatchCandidateResponse
)
from intelligence.graph.graph_models import IncidentGraph
from backend.services.cross_camera_engine import cross_camera_engine

router = APIRouter(prefix="/api/incidents", tags=["Cross-Camera Incidents & Incident Graph"])


@router.get("", response_model=List[IncidentResponse])
def get_all_incidents():
    """Returns all unified multi-camera incidents."""
    return cross_camera_engine.get_incidents()


@router.get("/candidates", response_model=List[MatchCandidateResponse])
def get_matching_candidates():
    """Returns recent cross-camera match candidate comparisons with factor breakdowns."""
    return cross_camera_engine.get_matching_candidates()


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident_detail(incident_id: str):
    """Returns summary for a specific incident."""
    incidents = cross_camera_engine.get_incidents()
    match = next((i for i in incidents if i.incident_id == incident_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return match


@router.get("/{incident_id}/timeline", response_model=List[IncidentTimelineEntry])
def get_incident_timeline(incident_id: str):
    """Returns the chronological multi-camera event and tracking timeline for an incident."""
    timeline = cross_camera_engine.get_incident_timeline(incident_id)
    if not timeline:
        raise HTTPException(status_code=404, detail=f"Timeline for incident '{incident_id}' not found")
    return timeline


@router.get("/{incident_id}/graph", response_model=IncidentGraph)
def get_incident_graph(incident_id: str):
    """Returns the complete serialized Incident Graph with typed nodes and relationship edges."""
    graph = cross_camera_engine.get_incident_graph(incident_id)
    if not graph:
        raise HTTPException(status_code=404, detail=f"Graph for incident '{incident_id}' not found")
    return graph
