from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class CameraTopologyResponse(BaseModel):
    relation_id: str
    source_camera: str
    destination_camera: str
    min_transition_seconds: float
    max_transition_seconds: float
    distance_meters: float
    direction: str
    enabled: bool
    description: Optional[str] = ""
    created_at: str


class CreateCameraTopologyRequest(BaseModel):
    source_camera: str
    destination_camera: str
    min_transition_seconds: float = 5.0
    max_transition_seconds: float = 180.0
    distance_meters: float = 50.0
    direction: str = "bidirectional"
    enabled: bool = True
    description: Optional[str] = ""


class SubjectTrackLinkResponse(BaseModel):
    id: int
    subject_id: str
    camera_id: str
    track_id: int
    formatted_track_id: str
    match_score: float
    match_status: str
    evidence: List[str] = []
    first_timestamp: str
    last_timestamp: str
    linked_at: str


class SubjectJourneyStep(BaseModel):
    sequence: int
    camera_id: str
    camera_name: str
    track_id: int
    formatted_track_id: str
    first_seen: str
    last_seen: str
    match_score: float
    match_status: str
    evidence: List[str] = []
    events_triggered: List[Dict[str, Any]] = []
    associated_vehicles: List[Dict[str, Any]] = []


class SubjectJourneyResponse(BaseModel):
    subject_id: str
    object_type: str
    first_seen: str
    last_seen: str
    total_cameras: int
    cameras_sequence: List[str]
    journey_steps: List[SubjectJourneyStep]


class SubjectResponse(BaseModel):
    subject_id: str
    object_type: str
    status: str
    first_seen: str
    last_seen: str
    initial_camera_id: str
    initial_track_id: int
    total_cameras_visited: int
    created_at: str
    track_links: List[SubjectTrackLinkResponse] = []


class IncidentTimelineEntry(BaseModel):
    timestamp: str
    camera_id: str
    camera_name: str
    entry_type: str  # OBSERVATION, ZONE_EVENT, MATCH_CONFIRMED, VEHICLE_ASSOCIATED
    title: str
    description: str
    track_id: int
    subject_id: str
    details: Dict[str, Any] = {}


class IncidentResponse(BaseModel):
    incident_id: str
    subject_id: str
    status: str
    title: str
    summary: str
    created_at: str
    updated_at: str
    cameras_involved: List[str] = []
    events_count: int = 0
    associated_vehicles_count: int = 0


class MatchCandidateResponse(BaseModel):
    source_camera: str
    source_track_id: int
    target_camera: str
    target_track_id: int
    object_type: str
    match_score: float
    match_status: str
    time_delta_seconds: float
    evidence: List[str] = []
    proposed_subject_id: Optional[str] = None


class AssociatedVehicleResponse(BaseModel):
    id: int
    subject_id: str
    vehicle_subject_id: str
    camera_id: str
    person_track_id: int
    vehicle_track_id: int
    relationship_type: str
    proximity_meters: float
    time_delta_seconds: float
    timestamp: str
    notes: str
