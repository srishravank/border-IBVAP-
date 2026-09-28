import cv2
import numpy as np
from ai.preprocessing.base_preprocessor import BaseFramePreprocessor


class IdentityPreprocessor(BaseFramePreprocessor):
    """Zero-overhead pass-through preprocessor."""

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        return frame


class LowLightPreprocessor(BaseFramePreprocessor):
    """
    Adaptive Low-Light & Night-Vision preprocessor for border surveillance feeds.
    Uses Contrast Limited Adaptive Histogram Equalization (CLAHE) on the luminance channel.
    """

    def __init__(self, clip_limit: float = 2.0, tile_grid_size: tuple = (8, 8), gamma: float = 1.2):
        self.clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        self.gamma = gamma
        self._gamma_lookup = self._build_gamma_lut(gamma)

    def _build_gamma_lut(self, gamma: float) -> np.ndarray:
        inv_gamma = 1.0 / gamma
        lut = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return lut

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        if frame is None or frame.size == 0:
            return frame

        # 1. Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # 2. Apply CLAHE to L-channel
        l_enhanced = self.clahe.apply(l)

        # 3. Apply Gamma correction if needed
        if self.gamma != 1.0:
            l_enhanced = cv2.LUT(l_enhanced, self._gamma_lookup)

        # 4. Merge back and convert to BGR
        enhanced_lab = cv2.merge((l_enhanced, a, b))
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
