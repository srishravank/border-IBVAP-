from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


class ObservedObjectSummary(BaseModel):
    """Summarized tracked entity within an AI Observation."""
    model_config = ConfigDict(populate_by_name=True)

    track_id: int = Field(..., description="Numeric track ID")
    formatted_id: str = Field(..., description="Formatted track ID (e.g. P001, V001)")
    type: str = Field(..., description="'person' or 'vehicle'")
    class_name: str = Field(..., alias="class", description="Class name ('person', 'car', etc.)")
    subclass: Optional[str] = Field(default=None, description="Subclass if vehicle")
    confidence: float = Field(..., description="Detection confidence score")
    bbox: List[float] = Field(..., description="[x1, y1, x2, y2] bounding box")
    center: List[float] = Field(..., description="[cx, cy] center coordinate")


class AIObservation(BaseModel):
    """
    Standardized Edge AI Observation object consumed by downstream Phase 3
    (virtual fences, zone breach verification, multi-frame filtering, evidence generation).
    """
    observation_id: str = Field(..., description="Unique observation ID (e.g. OBS-000104)")
    camera_id: str = Field(..., description="Origin camera identifier")
    frame_id: int = Field(..., description="Associated video frame sequence ID")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of the observation"
    )
    object: ObservedObjectSummary = Field(..., description="Primary tracked entity")
    trajectory: List[List[float]] = Field(default_factory=list, description="Recent trajectory trail points [[x, y], ...]")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Diagnostic and sensor metadata")
