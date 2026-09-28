from datetime import datetime, timezone
from typing import Optional
import cv2
import numpy as np
from pydantic import BaseModel, Field


class FrameMetadata(BaseModel):
    """Metadata attached to every captured CCTV video frame."""
    camera_id: str = Field(..., description="Unique identifier of the camera source")
    frame_id: int = Field(..., description="Monotonically increasing frame sequence number")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of frame capture"
    )
    width: int = Field(..., description="Width of the frame in pixels")
    height: int = Field(..., description="Height of the frame in pixels")
    fps: float = Field(default=25.0, description="Observed or target frame rate")
    source_type: str = Field(default="unknown", description="Source type (rtsp, file, webcam)")


class FramePacket:
    """
    High-performance Frame Packet containing both metadata and raw NumPy frame data.
    Designed for zero-copy handoff to future AI pipeline stages (YOLO/RT-DETR/ByteTrack).
    """
    __slots__ = ("metadata", "frame", "_cached_jpeg")

    def __init__(self, metadata: FrameMetadata, frame: np.ndarray):
        self.metadata: FrameMetadata = metadata
        self.frame: np.ndarray = frame
        self._cached_jpeg: Optional[bytes] = None

    def to_jpeg(self, quality: int = 75) -> bytes:
        """Encodes frame to JPEG format for MJPEG/HTTP preview streaming."""
        if self._cached_jpeg is not None:
            return self._cached_jpeg
        success, encoded = cv2.imencode(".jpg", self.frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if success:
            self._cached_jpeg = encoded.tobytes()
            return self._cached_jpeg
        return b""

    def to_dict(self) -> dict:
        return self.metadata.model_dump()
