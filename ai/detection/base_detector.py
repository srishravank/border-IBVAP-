from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np
from backend.models.detection import DetectionResult


class BaseObjectDetector(ABC):
    """
    Abstract Base Class for Edge AI Object Detectors.
    Provides a standardized interface for YOLO, RT-DETR, or custom neural networks.
    """

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.35,
        iou_threshold: float = 0.45,
        device: str = "auto"
    ):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.is_loaded: bool = False
        self.model_name: str = "BaseDetector"

    @abstractmethod
    def load_model(self) -> bool:
        """Loads and initializes the neural network weights into memory/device."""
        pass

    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """
        Executes inference on an input frame and returns filtered & normalized detections.
        """
        pass

    @abstractmethod
    def get_class_names(self) -> Dict[int, str]:
        """Returns the dictionary of class IDs to class label strings."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Returns diagnostic details regarding the loaded model, version, and device."""
        pass
