from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field


class DetectionResult(BaseModel):
    """
    Standardized bounding-box detection output from object detector.
    Normalizes person and vehicle categories.
    """
    class_name: str = Field(..., description="Detected class (e.g. 'person', 'car', 'motorcycle', 'bus', 'truck')")
    object_type: str = Field(..., description="Normalized object category ('person' or 'vehicle')")
    subclass: Optional[str] = Field(default=None, description="Vehicle subclass ('car', 'motorcycle', 'truck', 'bus') or None")
    confidence: float = Field(..., description="Detection confidence score (0.0 to 1.0)")
    bbox: List[float] = Field(..., description="Bounding box [x1, y1, x2, y2] in pixel coordinates")
    center: List[float] = Field(..., description="Center coordinate [cx, cy]")
    camera_id: Optional[str] = Field(default=None, description="Origin camera ID")
    frame_id: Optional[int] = Field(default=None, description="Frame sequence ID")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp")

    @property
    def x1(self) -> float:
        return self.bbox[0]

    @property
    def y1(self) -> float:
        return self.bbox[1]

    @property
    def x2(self) -> float:
        return self.bbox[2]

    @property
    def y2(self) -> float:
        return self.bbox[3]

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1


class DetectionSummary(BaseModel):
    total_detections: int = 0
    persons_count: int = 0
    vehicles_count: int = 0
    detections: List[DetectionResult] = []
