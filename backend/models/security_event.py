from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class SecurityEventType(str, Enum):
    ZONE_ENTRY = "ZONE_ENTRY"
    ZONE_EXIT = "ZONE_EXIT"
    ZONE_INTRUSION = "ZONE_INTRUSION"
    CAMERA_HEALTH = "CAMERA_HEALTH"


class EventStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    VERIFYING = "VERIFYING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    ACKNOWLEDGED = "ACKNOWLEDGED"


class VerificationDetail(BaseModel):
    required_frames: int = 3
    confirmed_frames: int = 1
    verification_status: str = "PENDING"  # PENDING, PASSED, FAILED, EXPIRED
    supporting_frame_ids: List[int] = []
    average_confidence: float = 0.0
    suppression_reasons: List[str] = []


class SecurityEventResponse(BaseModel):
    event_id: str
    camera_id: str
    track_id: int
    formatted_track_id: str
    zone_id: str
    zone_name: str
    event_type: SecurityEventType
    status: EventStatus
    created_at: str
    confirmed_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    confidence: float
    object_type: str
    class_name: str
    subclass: Optional[str] = None
    bbox: List[float]
    reference_point: List[float]
    trajectory: List[List[float]] = []
    verification: VerificationDetail
    description: str


class EventAcknowledgeRequest(BaseModel):
    operator_notes: Optional[str] = None
