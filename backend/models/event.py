from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    # Phase 1: Camera & Ingestion Health Events
    FRAME_RECEIVED = "FRAME_RECEIVED"
    CAMERA_ONLINE = "CAMERA_ONLINE"
    CAMERA_OFFLINE = "CAMERA_OFFLINE"
    CAMERA_RECONNECTING = "CAMERA_RECONNECTING"
    FRAME_FROZEN = "FRAME_FROZEN"
    INVALID_FRAME = "INVALID_FRAME"
    
    # Phase 2: Edge AI Detection & Tracking Events
    OBJECT_DETECTED = "OBJECT_DETECTED"
    OBJECT_TRACK_STARTED = "OBJECT_TRACK_STARTED"
    OBJECT_TRACK_UPDATED = "OBJECT_TRACK_UPDATED"
    OBJECT_TRACK_LOST = "OBJECT_TRACK_LOST"
    OBJECT_TRACK_REMOVED = "OBJECT_TRACK_REMOVED"
    
    # Phase 3+ Extensibility Placeholders
    VERIFICATION = "VERIFICATION"
    INTRUSION = "INTRUSION"
    RISK = "RISK"
    INCIDENT = "INCIDENT"
    EVIDENCE = "EVIDENCE"


class CameraEvent(BaseModel):
    """Event schema for camera status transitions, health alarms, and AI detection/tracking notifications."""
    event_type: EventType = Field(..., description="Type of the event")
    camera_id: str = Field(..., description="Camera ID that generated this event")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of the event"
    )
    frame_id: Optional[int] = Field(default=None, description="Optional frame ID associated with event")
    track_id: Optional[int] = Field(default=None, description="Optional track ID associated with event")
    object_type: Optional[str] = Field(default=None, description="Optional object category ('person' or 'vehicle')")
    confidence: Optional[float] = Field(default=None, description="Optional confidence score")
    message: Optional[str] = Field(default=None, description="Human-readable event description")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional structured diagnostic metadata")
