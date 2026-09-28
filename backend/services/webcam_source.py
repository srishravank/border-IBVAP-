import logging
from typing import Tuple, Optional, Dict, Any, Union
import cv2
import numpy as np
from backend.services.video_source import BaseVideoSource

logger = logging.getLogger("ibvap.source.webcam")


class WebcamSource(BaseVideoSource):
    """
    Webcam Video Source for development testing and rapid hardware verification.
    """

    def __init__(self, camera_id: str, device_index: Union[int, str] = 0, target_fps: float = 25.0):
        super().__init__(camera_id=camera_id, source_uri=str(device_index), target_fps=target_fps)
        try:
            self.device_index = int(device_index)
        except ValueError:
            self.device_index = 0
        self.cap: Optional[cv2.VideoCapture] = None

    def connect(self) -> bool:
        if self.cap is not None:
            self.cap.release()

        # On Windows, cv2.CAP_DSHOW provides rapid DirectShow initialisation
        self.cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            # Fallback to default backend
            self.cap = cv2.VideoCapture(self.device_index)

        if not self.cap.isOpened():
            logger.warning(f"[{self.camera_id}] Failed to open webcam device index: {self.device_index}")
            self._is_connected = False
            return False

        # Apply target resolution if requested
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        if self.target_fps > 0:
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        self.actual_fps = float(self.cap.get(cv2.CAP_PROP_FPS)) or 30.0
        self._is_connected = True
        logger.info(f"[{self.camera_id}] Connected to Webcam device index {self.device_index} ({self.width}x{self.height} @ {self.actual_fps:.1f} fps)")
        return True

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self._is_connected or self.cap is None:
            return False, None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            logger.warning(f"[{self.camera_id}] Failed to read frame from webcam {self.device_index}")
            return False, None

        return True, frame

    def is_connected(self) -> bool:
        return self._is_connected and self.cap is not None and self.cap.isOpened()

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "camera_id": self.camera_id,
            "source_type": "webcam",
            "source_uri": str(self.device_index),
            "is_connected": self.is_connected(),
            "width": self.width,
            "height": self.height,
            "actual_fps": self.actual_fps
        }

    def release(self) -> None:
        self._is_connected = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception as e:
                logger.error(f"[{self.camera_id}] Error releasing webcam: {e}")
            self.cap = None
        logger.info(f"[{self.camera_id}] Webcam source released")
