from enum import Enum
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class TrackState(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    LOST = "LOST"
    REMOVED = "REMOVED"


class TrackedObject(BaseModel):
    """
    Standardized model representing a persistent tracked entity across multiple frames.
    Includes observed trajectory history and track state lifecycle.
    """
    track_id: int = Field(..., description="Unique integer track ID for this camera")
    formatted_id: str = Field(..., description="Formatted track identifier (e.g. P001, V001)")
    camera_id: str = Field(..., description="Camera ID where track is active")
    object_type: str = Field(..., description="Normalized object category ('person' or 'vehicle')")
    class_name: str = Field(..., description="Specific class ('person', 'car', etc.)")
    subclass: Optional[str] = Field(default=None, description="Subclass for vehicles ('car', 'bus', 'truck', 'motorcycle')")
    confidence: float = Field(..., description="Latest detection confidence score")
    bbox: List[float] = Field(..., description="Current bounding box [x1, y1, x2, y2]")
    center: List[float] = Field(..., description="Current centroid coordinate [cx, cy]")
    trajectory: List[List[float]] = Field(default_factory=list, description="Recent trajectory history [[cx, cy], ...]")
    state: TrackState = Field(default=TrackState.ACTIVE, description="Lifecycle state (NEW, ACTIVE, LOST, REMOVED)")
    age: int = Field(default=1, description="Total number of frames track has existed")
    time_since_update: int = Field(default=0, description="Frames elapsed since last detection match")
    first_seen: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp when track was initialized"
    )
    last_seen: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of most recent frame update"
    )
    frame_id: int = Field(default=0, description="Latest observed frame ID")

    @classmethod
    def format_track_id(cls, object_type: str, track_id: int) -> str:
        prefix = "P" if object_type == "person" else "V"
        return f"{prefix}{track_id:03d}"
