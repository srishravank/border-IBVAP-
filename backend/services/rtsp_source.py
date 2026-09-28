import os
import logging
from typing import Tuple, Optional, Dict, Any
import cv2
import numpy as np
from backend.services.video_source import BaseVideoSource

logger = logging.getLogger("ibvap.source.rtsp")


class RTSPSource(BaseVideoSource):
    """
    RTSP Stream Source for industrial CCTV & IP Cameras.
    Configured for low-latency edge ingestion with TCP transport and minimal buffering.
    """

    def __init__(
        self,
        camera_id: str,
        rtsp_url: str,
        target_fps: float = 25.0,
        extra_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(camera_id=camera_id, source_uri=rtsp_url, target_fps=target_fps)
        self.rtsp_url = rtsp_url
        self.extra_config = extra_config or {}
        self.cap: Optional[cv2.VideoCapture] = None

    def _sanitize_url_for_logging(self, url: str) -> str:
        """Masks sensitive credentials in RTSP logs."""
        try:
            if "@" in url and "://" in url:
                proto, rest = url.split("://", 1)
                creds, host_path = rest.split("@", 1)
                return f"{proto}://***:***@{host_path}"
        except Exception:
            pass
        return url

    def connect(self) -> bool:
        if self.cap is not None:
            self.cap.release()

        # Optimize OpenCV FFmpeg backend for low-latency RTSP
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|analyzeduration;1000000|probesize;1000000"

        sanitized = self._sanitize_url_for_logging(self.rtsp_url)
        logger.info(f"[{self.camera_id}] Connecting to RTSP stream: {sanitized}")

        self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        if not self.cap.isOpened():
            # Fallback try
            self.cap = cv2.VideoCapture(self.rtsp_url)

        if not self.cap.isOpened():
            logger.warning(f"[{self.camera_id}] Failed to open RTSP stream: {sanitized}")
            self._is_connected = False
            return False

        # Set buffer size to 1 frame to prevent lag/stale frames
        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
        self.actual_fps = float(self.cap.get(cv2.CAP_PROP_FPS)) or self.target_fps
        self._is_connected = True
        logger.info(f"[{self.camera_id}] Connected to RTSP stream ({self.width}x{self.height} @ {self.actual_fps:.1f} fps)")
        return True

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self._is_connected or self.cap is None:
            return False, None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            logger.warning(f"[{self.camera_id}] Failed to read frame from RTSP stream")
            return False, None

        return True, frame

    def is_connected(self) -> bool:
        return self._is_connected and self.cap is not None and self.cap.isOpened()

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "camera_id": self.camera_id,
            "source_type": "rtsp",
            "source_uri": self._sanitize_url_for_logging(self.rtsp_url),
            "is_connected": self.is_connected(),
            "width": self.width,
            "height": self.height,
            "actual_fps": self.actual_fps,
            "extra_config": self.extra_config
        }

    def release(self) -> None:
        self._is_connected = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception as e:
                logger.error(f"[{self.camera_id}] Error releasing RTSP stream: {e}")
            self.cap = None
        logger.info(f"[{self.camera_id}] RTSP source released")
