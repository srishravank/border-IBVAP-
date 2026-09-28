from typing import List, Dict, Any
import numpy as np
from ai.detection.base_detector import BaseObjectDetector
from backend.models.detection import DetectionResult


class MockDetector(BaseObjectDetector):
    """
    Deterministic Mock Detector for testing, verification, and offline test environments.
    Produces predictable person and vehicle detections across successive frames.
    """

    def __init__(
        self,
        model_path: str = "mock",
        confidence_threshold: float = 0.35,
        iou_threshold: float = 0.45,
        device: str = "cpu"
    ):
        super().__init__(model_path, confidence_threshold, iou_threshold, device)
        self.step = 0
        self.model_name = "MockDeterministicDetector"

    def load_model(self) -> bool:
        self.is_loaded = True
        return True

    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        if not self.is_loaded or frame is None or frame.size == 0:
            return []

        self.step += 1
        h, w = frame.shape[:2]
        
        # Moving simulated person target
        p_x1 = 200.0 + (self.step * 5) % 400
        p_y1 = 150.0 + (self.step * 2) % 200
        p_x2 = p_x1 + 80.0
        p_y2 = p_y1 + 180.0
        
        # Moving simulated vehicle target
        v_x1 = 600.0 + (self.step * 8) % 500
        v_y1 = 350.0
        v_x2 = v_x1 + 220.0
        v_y2 = v_y1 + 120.0

        detections = [
            DetectionResult(
                class_name="person",
                object_type="person",
                subclass=None,
                confidence=0.92,
                bbox=[p_x1, p_y1, p_x2, p_y2],
                center=[(p_x1 + p_x2) / 2.0, (p_y1 + p_y2) / 2.0]
            ),
            DetectionResult(
                class_name="car",
                object_type="vehicle",
                subclass="car",
                confidence=0.88,
                bbox=[v_x1, v_y1, v_x2, v_y2],
                center=[(v_x1 + v_x2) / 2.0, (v_y1 + v_y2) / 2.0]
            )
        ]

        return [d for d in detections if d.confidence >= self.confidence_threshold]

    def get_class_names(self) -> Dict[int, str]:
        return {0: "person", 1: "car", 2: "motorcycle", 3: "bus", 4: "truck"}

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_type": "Mock",
            "model_name": self.model_name,
            "device": "cpu",
            "confidence_threshold": self.confidence_threshold,
            "is_loaded": self.is_loaded
        }
