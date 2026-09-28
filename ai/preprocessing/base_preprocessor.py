from abc import ABC, abstractmethod
import numpy as np


class BaseFramePreprocessor(ABC):
    """Abstract interface for video frame preprocessing (e.g. low-light enhancement, color normalization)."""

    @abstractmethod
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocesses an incoming BGR frame prior to passing to object detection.
        Returns the preprocessed BGR frame.
        """
        pass
