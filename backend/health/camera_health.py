import time
import logging
from typing import Optional, Callable, Dict, Any, List
import cv2
import numpy as np
from backend.models.camera import CameraStatus
from backend.models.event import CameraEvent, EventType
from backend.config import settings

logger = logging.getLogger("ibvap.health")


class CameraHealthMonitor:
    """
    Monitors stream liveness, frame integrity, and detects failure modes:
    - OFFLINE: stream disconnected / read failure
    - FROZEN: video frozen / unchanging pixels for > threshold seconds
    - BLACK_FRAME: dark/black or obscured optical feed
    - RECOVERING: reconnection underway
    - ONLINE: healthy stream
    """

    def __init__(
        self,
        camera_id: str,
        on_event_callback: Optional[Callable[[CameraEvent], None]] = None,
        frozen_seconds_threshold: float = settings.FROZEN_FRAME_THRESHOLD_SECONDS,
        frozen_diff_threshold: float = settings.FROZEN_DIFF_THRESHOLD,
        black_mean_threshold: float = settings.BLACK_FRAME_MEAN_THRESHOLD,
        black_std_threshold: float = settings.BLACK_FRAME_STD_THRESHOLD,
    ):
        self.camera_id = camera_id
        self.on_event_callback = on_event_callback
        
        self.frozen_seconds_threshold = frozen_seconds_threshold
        self.frozen_diff_threshold = frozen_diff_threshold
        self.black_mean_threshold = black_mean_threshold
        self.black_std_threshold = black_std_threshold

        self.current_status: CameraStatus = CameraStatus.OFFLINE
        self.last_frame_time: Optional[float] = None
        self.first_connected_time: Optional[float] = None
        
        # Frozen detection state
        self._prev_thumbnail: Optional[np.ndarray] = None
        self._unchanged_since: Optional[float] = None
        
        # FPS calculation state (rolling 1 second window)
        self._frame_timestamps: List[float] = []
        self.current_fps: float = 0.0
        self.total_frames_received: int = 0
        self.reconnect_attempts: int = 0
        self.last_error_message: str = ""

    def _emit_event(self, event_type: EventType, message: str, frame_id: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        """Dispatches health events to registered event handlers and logs state changes."""
        event = CameraEvent(
            event_type=event_type,
            camera_id=self.camera_id,
            frame_id=frame_id,
            message=message,
            details=details or {}
        )
        level = logging.WARNING if event_type in (EventType.CAMERA_OFFLINE, EventType.FRAME_FROZEN, EventType.INVALID_FRAME) else logging.INFO
        logger.log(level, f"[{self.camera_id}] [{event_type.value}] {message}")
        
        if self.on_event_callback:
            try:
                self.on_event_callback(event)
            except Exception as e:
                logger.error(f"[{self.camera_id}] Exception in health event callback: {e}")

    def set_status(self, new_status: CameraStatus, reason: str = ""):
        """Transitions camera status and publishes corresponding event."""
        if self.current_status != new_status:
            old_status = self.current_status
            self.current_status = new_status
            
            if new_status == CameraStatus.ONLINE:
                if self.first_connected_time is None:
                    self.first_connected_time = time.time()
                self._emit_event(
                    EventType.CAMERA_ONLINE,
                    f"Camera stream active (transitioned from {old_status.value})"
                )
            elif new_status == CameraStatus.OFFLINE:
                self.last_error_message = reason or "Stream disconnected"
                self._emit_event(
                    EventType.CAMERA_OFFLINE,
                    f"Camera disconnected: {self.last_error_message}"
                )
            elif new_status == CameraStatus.RECONNECTING:
                self.reconnect_attempts += 1
                self._emit_event(
                    EventType.CAMERA_RECONNECTING,
                    f"Reconnection attempt #{self.reconnect_attempts}: {reason}"
                )
            elif new_status == CameraStatus.FROZEN:
                self._emit_event(
                    EventType.FRAME_FROZEN,
                    f"Camera video stream is frozen (> {self.frozen_seconds_threshold:.1f}s without pixel change)"
                )
            elif new_status == CameraStatus.BLACK_FRAME:
                self._emit_event(
                    EventType.INVALID_FRAME,
                    "Camera feed is black / empty or lens obstructed"
                )

    def process_frame(self, frame: np.ndarray, frame_id: int) -> CameraStatus:
        """
        Inspects an incoming frame for health anomalies (frozen, black/empty).
        Updates FPS, frame counters, and status.
        """
        now = time.time()
        self.last_frame_time = now
        self.total_frames_received += 1

        # Track rolling FPS
        self._frame_timestamps.append(now)
        self._frame_timestamps = [t for t in self._frame_timestamps if now - t <= 1.0]
        self.current_fps = round(len(self._frame_timestamps), 1)

        # 1. Black / Empty Frame check
        # Downsample to small grayscale 64x36 for instant performance
        gray_thumb = cv2.resize(frame, (64, 36), interpolation=cv2.INTER_AREA)
        if len(gray_thumb.shape) == 3:
            gray_thumb = cv2.cvtColor(gray_thumb, cv2.COLOR_BGR2GRAY)

        mean_val = float(np.mean(gray_thumb))
        std_val = float(np.std(gray_thumb))

        if mean_val < self.black_mean_threshold and std_val < self.black_std_threshold:
            if self.current_status != CameraStatus.BLACK_FRAME:
                self.set_status(CameraStatus.BLACK_FRAME, f"Mean luminance {mean_val:.2f} < {self.black_mean_threshold}")
            return self.current_status

        # 2. Frozen Frame check
        if self._prev_thumbnail is not None:
            diff = float(np.mean(np.abs(gray_thumb.astype(np.float32) - self._prev_thumbnail.astype(np.float32))))
            if diff < self.frozen_diff_threshold:
                if self._unchanged_since is None:
                    self._unchanged_since = getattr(self, "_prev_thumbnail_time", now)
                
                if (now - self._unchanged_since) >= self.frozen_seconds_threshold:
                    if self.current_status != CameraStatus.FROZEN:
                        self.set_status(CameraStatus.FROZEN, f"No change for {(now - self._unchanged_since):.1f}s")
                    return self.current_status
            else:
                self._unchanged_since = None
                self._prev_thumbnail = gray_thumb
                self._prev_thumbnail_time = now
                if self.current_status in (CameraStatus.FROZEN, CameraStatus.BLACK_FRAME, CameraStatus.OFFLINE, CameraStatus.RECONNECTING):
                    self.set_status(CameraStatus.ONLINE, "Stream recovered normal activity")
        else:
            self._prev_thumbnail = gray_thumb
            self._prev_thumbnail_time = now
            self._unchanged_since = None
            if self.current_status != CameraStatus.ONLINE:
                self.set_status(CameraStatus.ONLINE, "First valid frame received")

        return self.current_status

    def record_disconnect(self, reason: str = ""):
        """Called when stream read encounters an error or EOF."""
        self._prev_thumbnail = None
        self._unchanged_since = None
        self.set_status(CameraStatus.OFFLINE, reason)

    def record_reconnecting(self, reason: str = ""):
        """Called when reconnection sequence starts."""
        self.set_status(CameraStatus.RECONNECTING, reason)

    def get_uptime_seconds(self) -> float:
        if self.first_connected_time and self.current_status == CameraStatus.ONLINE:
            return round(time.time() - self.first_connected_time, 1)
        return 0.0

    def reset_reconnect_counter(self):
        self.reconnect_attempts = 0
