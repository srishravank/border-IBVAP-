import os
import time
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import cv2
import numpy as np
from backend.services.video_source import BaseVideoSource
from backend.config import BASE_DIR

logger = logging.getLogger("ibvap.source.file")


class FileSource(BaseVideoSource):
    """
    Video File Source for simulating CCTV cameras using recorded border surveillance footage.
    Includes automated looping and timing control for realistic frame rates.
    """

    def __init__(self, camera_id: str, file_path: str, loop: bool = True, target_fps: float = 25.0):
        super().__init__(camera_id=camera_id, source_uri=file_path, target_fps=target_fps)
        self.file_path = file_path
        self.loop = loop
        self.cap: Optional[cv2.VideoCapture] = None
        self.total_frames: int = 0
        self.current_frame_pos: int = 0
        self._last_frame_time: float = 0.0

    def _resolve_path(self) -> str:
        """Resolves path relative to project root if not absolute, stripping any quotes and whitespace."""
        clean_path = str(self.file_path).strip().strip('"\'').strip()
        p = Path(clean_path)
        if p.is_absolute() and p.exists():
            return str(p)
        
        # Check project BASE_DIR relative
        base_path = BASE_DIR / clean_path
        if base_path.exists():
            return str(base_path)

        # Check data/videos/ relative
        videos_path = BASE_DIR / "data" / "videos" / clean_path
        if videos_path.exists():
            return str(videos_path)

        # Check workspace relative
        ws_path = Path.cwd() / clean_path
        if ws_path.exists():
            return str(ws_path)

        # Direct path fallback
        return str(p)

    def connect(self) -> bool:
        resolved_path = self._resolve_path()
        if not os.path.exists(resolved_path):
            logger.warning(f"[{self.camera_id}] Video file not found: {resolved_path}")
            self._is_connected = False
            return False

        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass

        self.cap = cv2.VideoCapture(resolved_path)
        if not self.cap.isOpened():
            logger.error(f"[{self.camera_id}] Failed to open video file: {resolved_path}")
            self._is_connected = False
            return False

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
        self.actual_fps = float(self.cap.get(cv2.CAP_PROP_FPS)) or self.target_fps
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._is_connected = True
        logger.info(f"[{self.camera_id}] Connected to file: {resolved_path} ({self.width}x{self.height} @ {self.actual_fps:.1f} fps, {self.total_frames} frames)")
        return True

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
        self.actual_fps = float(self.cap.get(cv2.CAP_PROP_FPS)) or self.target_fps
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._is_connected = True
        logger.info(f"[{self.camera_id}] Connected to file: {resolved_path} ({self.width}x{self.height} @ {self.actual_fps:.1f} fps, {self.total_frames} frames)")
        return True

    def _generate_synthetic_frame(self) -> np.ndarray:
        """Procedurally renders a tactical border surveillance CCTV frame."""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # Background gradient (dark night surveillance)
        frame[:, :] = (15, 20, 25)

        # Draw grid reticle
        for x in range(0, self.width, 80):
            cv2.line(frame, (x, 0), (x, self.height), (30, 40, 50), 1)
        for y in range(0, self.height, 80):
            cv2.line(frame, (0, y), (self.width, y), (30, 40, 50), 1)

        # Ground border line
        ground_y = int(self.height * 0.75)
        cv2.line(frame, (0, ground_y), (self.width, ground_y), (40, 55, 65), 2)

        # Animated simulated border patrol agent / target
        t = (self.current_frame_pos % 300) / 300.0
        agent_x = int(150 + t * (self.width - 300))
        agent_y = int(ground_y - 60 - np.sin(t * np.pi * 4) * 8)
        
        # Person silhouette / IR heat signature box
        cv2.rectangle(frame, (agent_x - 15, agent_y - 50), (agent_x + 15, agent_y + 40), (80, 180, 240), 2)
        cv2.circle(frame, (agent_x, agent_y - 35), 10, (100, 200, 255), -1)
        cv2.putText(frame, "TARGET-SIM", (agent_x - 30, agent_y - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 220, 255), 1)

        # Timestamp and OSD HUD
        ts_str = time.strftime("%Y-%m-%d %H:%M:%S UTC")
        cv2.putText(frame, f"[{self.camera_id}] BORDER SECTOR SENSOR (SYNTHETIC FEED)", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 255), 2)
        cv2.putText(frame, f"TIME: {ts_str} | FRAME: {self.current_frame_pos:06d}", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 190, 200), 1)

        return frame

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self._is_connected or self.cap is None or not self.cap.isOpened():
            return False, None

        # Frame rate timing throttle for simulated playback
        if self.target_fps > 0:
            frame_interval = 1.0 / self.target_fps
            elapsed = time.time() - self._last_frame_time
            if elapsed < frame_interval:
                time.sleep(max(0.001, frame_interval - elapsed))

        self._last_frame_time = time.time()
        self.current_frame_pos += 1

        ret, frame = self.cap.read()

        if not ret or frame is None:
            if self.loop and self.total_frames > 0:
                # Rewind video to beginning for continuous CCTV simulation
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    return True, frame
            logger.warning(f"[{self.camera_id}] End of video stream or unreadable frame")
            return False, None

        return True, frame

    def is_connected(self) -> bool:
        return self._is_connected

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "camera_id": self.camera_id,
            "source_type": "file",
            "source_uri": self.file_path,
            "is_connected": self.is_connected(),
            "width": self.width,
            "height": self.height,
            "actual_fps": self.actual_fps,
            "total_frames": self.total_frames,
            "current_frame_pos": self.current_frame_pos
        }

    def release(self) -> None:
        self._is_connected = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception as e:
                logger.error(f"[{self.camera_id}] Error releasing video capture: {e}")
            self.cap = None
        logger.info(f"[{self.camera_id}] File source released")
