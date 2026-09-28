from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DashboardSummaryResponse(BaseModel):
    """Real-time system overview for the SOC Command Center."""
    total_cameras: int = 0
    online_cameras: int = 0
    offline_cameras: int = 0
    degraded_cameras: int = 0
    alert_cameras: int = 0

    total_incidents: int = 0
    active_incidents: int = 0
    critical_risk_incidents: int = 0
    high_risk_incidents: int = 0
    medium_risk_incidents: int = 0
    low_risk_incidents: int = 0
    closed_incidents: int = 0

    sectors_count: int = 0
    sectors_with_alerts: int = 0
    active_tracks_count: int = 0
    timestamp: str


class SectorRiskSummary(BaseModel):
    """Risk summary per border sector."""
    sector_id: str
    sector_name: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    max_risk_score: float = 0.0
    active_incidents_count: int = 0
    camera_ids: List[str] = []
    cameras_online: int = 0
    cameras_total: int = 0
    has_active_intrusion: bool = False
    description: Optional[str] = ""


class RecommendedCameraResponse(BaseModel):
    """Explainable recommended nearby or forward-route cameras for active tracking."""
    camera_id: str
    camera_name: str
    location: str
    reason: str
    relationship: str  # JOURNEY_CONTINUATION, TOPOLOGY_NEIGHBOR, SPATIAL_PROXIMITY, RECENT_ACTIVITY
    distance_meters: Optional[float] = None
    expected_transit_window: Optional[str] = None


class OperatorActionRequest(BaseModel):
    """Payload for submitting an operator action."""
    operator_id: str = "OP-001"
    role: str = "OPERATOR"  # OPERATOR, SUPERVISOR, INVESTIGATOR, ADMIN
    action: str  # ACKNOWLEDGE, INVESTIGATE, CLOSE, ADD_NOTE, FOCUS_CAMERA
    notes: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = {}


class OperatorActionResponse(BaseModel):
    """Persisted operator action audit trail record."""
    action_id: str
    incident_id: str
    operator_id: str
    role: str
    action: str
    notes: Optional[str] = ""
    metadata: Dict[str, Any] = {}
    timestamp: str


class IncidentNoteRequest(BaseModel):
    """Payload for adding an operator investigation note."""
    operator_id: str = "OP-001"
    role: str = "OPERATOR"
    note: str


class IncidentNoteResponse(BaseModel):
    """Persisted operator note."""
    note_id: str
    incident_id: str
    operator_id: str
    role: str
    note: str
    timestamp: str


class LifecycleStageStatus(BaseModel):
    """Status of an individual stage in the IBVAP 2.0 lifecycle."""
    stage: str  # DETECTED, VERIFIED, CORRELATED, ASSESSED, ACKNOWLEDGED, INVESTIGATING, CLOSED
    is_completed: bool
    is_current: bool
    completed_at: Optional[str] = None
    operator_id: Optional[str] = None
    description: str = ""


class IncidentStatusHistoryItem(BaseModel):
    """Single entry in the status transition history."""
    previous_status: str
    new_status: str
    changed_by: str
    role: str
    notes: Optional[str] = ""
    timestamp: str


class IncidentLifecycleResponse(BaseModel):
    """Full lifecycle view of an incident."""
    incident_id: str
    subject_id: str
    current_status: str
    stages: List[LifecycleStageStatus]
    history: List[IncidentStatusHistoryItem] = []


class IncidentNarrativeResponse(BaseModel):
    """Machine-generated explainable narrative using strictly neutral, verified facts."""
    incident_id: str
    subject_id: str
    risk_level: str
    risk_score: float
    narrative: str
    key_facts: List[str] = []
    generated_at: str


class CommandAlertResponse(BaseModel):
    """Real-time operational alert for human operators."""
    alert_id: str
    incident_id: str
    subject_id: str
    risk_level: str
    risk_score: float
    camera_id: str
    camera_name: str
    zone_name: Optional[str] = "Border Corridor"
    message: str
    timestamp: str
    is_acknowledged: bool = False
