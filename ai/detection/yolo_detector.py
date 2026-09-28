import os
import logging
import threading
from typing import List, Dict, Any, Optional
import numpy as np
import torch

from ai.detection.base_detector import BaseObjectDetector
from backend.models.detection import DetectionResult

logger = logging.getLogger("ibvap.ai.yolo")

# Target surveillance COCO classes: person (0), bicycle (1), car (2), motorcycle (3), bus (5), truck (7), etc.
VEHICLE_SUBCLASSES = {"car", "motorcycle", "bus", "truck", "bicycle", "train", "airplane", "boat"}
ANIMAL_SUBCLASSES = {"bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"}
OBJECT_SUBCLASSES = {"backpack", "umbrella", "handbag", "suitcase"}


class YOLODetector(BaseObjectDetector):
    """
    YOLO Object Detector (supports YOLOv8, YOLOv9, YOLOv11).
    Optimized for edge border surveillance perception with thread-safe multi-camera inference.
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.35,
        iou_threshold: float = 0.45,
        device: str = "auto"
    ):
        super().__init__(
            model_path=model_path,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
            device=device
        )
        self.model = None
        self.model_name = "YOLO"
        self._resolved_device = "cpu"
        self.class_names: Dict[int, str] = {}
        self._predict_lock = threading.Lock()

    def _resolve_device(self) -> str:
        if self.device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return self.device

    def load_model(self) -> bool:
        """Initializes and loads the YOLO neural network."""
        try:
            from ultralytics import YOLO
            self._resolved_device = self._resolve_device()
            logger.info(f"Loading YOLO model '{self.model_path}' on device: {self._resolved_device}...")
            
            # Restrict torch threads on CPU to avoid thread thrashing across multiple camera workers
            if self._resolved_device == "cpu":
                torch.set_num_threads(2)

            # Load model (Ultralytics handles local file or auto-download on first load)
            self.model = YOLO(self.model_path)
            self.class_names = self.model.names if hasattr(self.model, "names") else {}
            self.is_loaded = True
            self.model_name = f"YOLO ({os.path.basename(self.model_path)})"
            logger.info(f"YOLO model loaded successfully. Detected {len(self.class_names)} classes.")
            return True
        except Exception as e:
            logger.error(f"Failed to load YOLO model '{self.model_path}': {e}")
            self.is_loaded = False
            self.model = None
            return False

    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """Runs YOLO inference on a BGR frame and returns normalized detections."""
        if not self.is_loaded or self.model is None or frame is None or frame.size == 0:
            return []

        try:
            with self._predict_lock:
                # Run thread-safe inference with optimized resolution for multi-stream CPU/GPU
                results = self.model.predict(
                    source=frame,
                    conf=self.confidence_threshold,
                    iou=self.iou_threshold,
                    device=self._resolved_device,
                    imgsz=640,
                    verbose=False
                )

            detections: List[DetectionResult] = []
            if not results or len(results) == 0:
                return detections

            boxes = results[0].boxes
            if boxes is None or len(boxes) == 0:
                return detections

            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                raw_name = self.class_names.get(cls_id, str(cls_id)).lower()

                # Normalize class into Person / Vehicle / Animal / Object categories
                if raw_name == "person":
                    obj_type = "person"
                    subclass = None
                    norm_class = "person"
                elif raw_name in VEHICLE_SUBCLASSES:
                    obj_type = "vehicle"
                    subclass = raw_name
                    norm_class = raw_name
                elif raw_name in ANIMAL_SUBCLASSES:
                    obj_type = "animal"
                    subclass = raw_name
                    norm_class = raw_name
                elif raw_name in OBJECT_SUBCLASSES:
                    obj_type = "object"
                    subclass = raw_name
                    norm_class = raw_name
                else:
                    # Ignore non-surveillance categories (e.g. indoor furniture/appliances)
                    continue

                xyxy = box.xyxy[0].cpu().numpy().tolist()
                x1, y1, x2, y2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])
                cx = float((x1 + x2) / 2.0)
                cy = float((y1 + y2) / 2.0)

                detections.append(
                    DetectionResult(
                        class_name=norm_class,
                        object_type=obj_type,
                        subclass=subclass,
                        confidence=round(conf, 3),
                        bbox=[round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                        center=[round(cx, 1), round(cy, 1)]
                    )
                )

            return detections

        except Exception as e:
            logger.error(f"YOLO detection exception: {e}")
            return []

    def get_class_names(self) -> Dict[int, str]:
        return self.class_names

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_type": "YOLO",
            "model_name": self.model_name,
            "model_path": self.model_path,
            "device": self._resolved_device,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "is_loaded": self.is_loaded
        }
