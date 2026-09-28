import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import torch

from ai.detection.base_detector import BaseObjectDetector
from backend.models.detection import DetectionResult

logger = logging.getLogger("ibvap.ai.rtdetr")

VEHICLE_SUBCLASSES = {"car", "motorcycle", "bus", "truck", "bicycle"}


class RTDETRDetector(BaseObjectDetector):
    """
    RT-DETR (Real-Time DEtection TRansformer) Object Detector.
    High-accuracy edge vision transformer detector.
    """

    def __init__(
        self,
        model_path: str = "rtdetr-l.pt",
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
        self.model_name = "RT-DETR"
        self._resolved_device = "cpu"
        self.class_names: Dict[int, str] = {}

    def _resolve_device(self) -> str:
        if self.device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return self.device

    def load_model(self) -> bool:
        try:
            from ultralytics import RTDETR
            self._resolved_device = self._resolve_device()
            logger.info(f"Loading RT-DETR model '{self.model_path}' on device: {self._resolved_device}...")
            self.model = RTDETR(self.model_path)
            self.class_names = self.model.names if hasattr(self.model, "names") else {}
            self.is_loaded = True
            self.model_name = f"RT-DETR ({os.path.basename(self.model_path)})"
            logger.info("RT-DETR model loaded successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to load RT-DETR model '{self.model_path}': {e}")
            self.is_loaded = False
            self.model = None
            return False

    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        if not self.is_loaded or self.model is None or frame is None or frame.size == 0:
            return []

        try:
            results = self.model.predict(
                source=frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                device=self._resolved_device,
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

                if raw_name == "person":
                    obj_type = "person"
                    subclass = None
                    norm_class = "person"
                elif raw_name in VEHICLE_SUBCLASSES:
                    obj_type = "vehicle"
                    subclass = raw_name
                    norm_class = raw_name
                else:
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
            logger.error(f"RT-DETR detection error: {e}")
            return []

    def get_class_names(self) -> Dict[int, str]:
        return self.class_names

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_type": "RT-DETR",
            "model_name": self.model_name,
            "model_path": self.model_path,
            "device": self._resolved_device,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "is_loaded": self.is_loaded
        }
