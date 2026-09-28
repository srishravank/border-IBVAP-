from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any
import numpy as np


class BaseVideoSource(ABC):
    """
    Abstract Base Class for all CCTV video ingestion sources.
    Provides a unified interface for RTSP streams, local video files, and webcams.
    """

    def __init__(self, camera_id: str, source_uri: str, target_fps: float = 25.0):
        self.camera_id: str = camera_id
        self.source_uri: str = source_uri
        self.target_fps: float = target_fps
        self._is_connected: bool = False
        self.width: int = 0
        self.height: int = 0
        self.actual_fps: float = 0.0

    @abstractmethod
    def connect(self) -> bool:
        """
        Establishes connection / opens stream with the video source.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Grabs and returns the next frame from the video source.
        Returns:
            Tuple[bool, Optional[np.ndarray]]: (success, frame_bgr)
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Returns True if the underlying video stream is active and readable."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Returns resolution, native fps, and source diagnostics."""
        pass

    @abstractmethod
    def release(self) -> None:
        """Releases underlying capture resources and socket/file handles."""
        pass
