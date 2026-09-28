from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CameraSourceType(str, Enum):
    RTSP = "rtsp"
    FILE = "file"
    WEBCAM = "webcam"


class CameraStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    RECONNECTING = "RECONNECTING"
    FROZEN = "FROZEN"
    BLACK_FRAME = "BLACK_FRAME"


from pydantic import BaseModel, Field, field_validator


class CameraBase(BaseModel):
    camera_name: str = Field(..., description="Human-readable camera name", json_schema_extra={"example": "Sector A Gate Camera"})
    location: str = Field(..., description="Border sector or installation point", json_schema_extra={"example": "Sector A - Gate 1"})
    source_type: CameraSourceType = Field(..., description="Ingestion protocol or source type")
    source: str = Field(..., description="RTSP URL, file path, or webcam index", json_schema_extra={"example": "data/videos/camera01.mp4"})
    enabled: bool = Field(default=True, description="Whether camera ingestion should be enabled")
    description: Optional[str] = Field(default="", description="Optional remarks or notes")
    target_fps: Optional[float] = Field(default=25.0, description="Target ingestion frame rate")
    frame_width: Optional[int] = Field(default=1280, description="Target frame width")
    frame_height: Optional[int] = Field(default=720, description="Target frame height")
    extra_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="ONVIF/RTSP credentials or custom camera parameters"
    )

    @field_validator("source", mode="before")
    @classmethod
    def sanitize_source(cls, v: Any) -> str:
        if isinstance(v, str):
            # Strip quotes and leading/trailing whitespace
            return v.strip().strip('"\'').strip()
        return str(v)


class CameraConfigCreate(CameraBase):
    camera_id: str = Field(..., description="Unique alphanumeric identifier (e.g. CAM-01)", json_schema_extra={"example": "CAM-01"})

    @field_validator("camera_id", mode="before")
    @classmethod
    def sanitize_camera_id(cls, v: Any) -> str:
        if isinstance(v, str):
            # Strip spaces, replace internal spaces/hyphens with single hyphen, and uppercase
            import re
            cleaned = re.sub(r'[\s\-]+', '-', v.strip()).strip('-').upper()
            return cleaned or v.strip().upper()
        return str(v)


class CameraConfigUpdate(BaseModel):
    camera_name: Optional[str] = None
    location: Optional[str] = None
    source_type: Optional[CameraSourceType] = None
    source: Optional[str] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None
    target_fps: Optional[float] = None
    frame_width: Optional[int] = None
    frame_height: Optional[int] = None
    extra_config: Optional[Dict[str, Any]] = None


class CameraResponse(CameraBase):
    camera_id: str
    status: CameraStatus = CameraStatus.OFFLINE
    last_seen: Optional[str] = None
    created_at: str
    fps: float = 0.0
    actual_width: Optional[int] = None
    actual_height: Optional[int] = None
    total_frames_ingested: int = 0
    reconnect_attempts: int = 0


class CameraStatusResponse(BaseModel):
    camera_id: str
    camera_name: str
    status: CameraStatus
    source_type: CameraSourceType
    source: str
    is_ingesting: bool
    fps: float
    resolution: str
    last_frame_timestamp: Optional[str] = None
    total_frames_ingested: int = 0
    reconnect_attempts: int = 0
    health_message: str = "Normal"
    uptime_seconds: float = 0.0
