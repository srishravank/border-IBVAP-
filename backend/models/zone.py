from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ZoneType(str, Enum):
    RESTRICTED = "restricted"
    EXCLUSION = "exclusion"
    CHECKPOINT = "checkpoint"
    ENTRY_CORRIDOR = "entry_corridor"


class ZoneSensitivity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ZoneBase(BaseModel):
    zone_name: str = Field(..., description="Human-readable zone name", json_schema_extra={"example": "Sector A Restricted Border Fence"})
    zone_type: ZoneType = Field(default=ZoneType.RESTRICTED, description="Category of virtual zone")
    polygon: List[List[float]] = Field(..., description="List of [x, y] vertex coordinates in image pixel space (min 3 points)", json_schema_extra={"example": [[100, 100], [600, 100], [600, 400], [100, 400]]})
    enabled: bool = Field(default=True, description="Whether zone rule evaluation is active")
    sensitivity: ZoneSensitivity = Field(default=ZoneSensitivity.HIGH, description="Sensitivity level")
    description: Optional[str] = Field(default="", description="Optional remarks or border sector notes")
    color: Optional[str] = Field(default="#F43F5E", description="Hex color for visualization")


class ZoneCreate(ZoneBase):
    camera_id: str = Field(..., description="Camera ID to associate with this virtual zone", json_schema_extra={"example": "CAM-01"})
    zone_id: Optional[str] = Field(default=None, description="Optional custom Zone ID (auto-generated if omitted)", json_schema_extra={"example": "ZONE-CAM01-01"})


class ZoneUpdate(BaseModel):
    zone_name: Optional[str] = None
    zone_type: Optional[ZoneType] = None
    polygon: Optional[List[List[float]]] = None
    enabled: Optional[bool] = None
    sensitivity: Optional[ZoneSensitivity] = None
    description: Optional[str] = None
    color: Optional[str] = None


class ZoneResponse(ZoneBase):
    zone_id: str
    camera_id: str
    created_at: str
