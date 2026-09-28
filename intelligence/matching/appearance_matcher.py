import cv2
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, List, Union


class BaseAppearanceMatcher(ABC):
    """
    Abstract interface for cross-camera appearance matching.
    Provides pluggable representation for lightweight color/spatial histograms,
    deep re-ID embeddings, or synthetic visual feature vectors.
    """

    @abstractmethod
    def extract_features(self, crop: Optional[np.ndarray], metadata: Optional[dict] = None) -> np.ndarray:
        """Extracts a normalized feature vector from a bounding box crop or observation metadata."""
        pass

    @abstractmethod
    def compute_similarity(self, feat_a: np.ndarray, feat_b: np.ndarray) -> float:
        """Computes similarity score in range [0.0, 1.0] between two feature vectors."""
        pass


class HistogramAppearanceMatcher(BaseAppearanceMatcher):
    """
    Practical, lightweight multi-region HSV color and spatial histogram matcher.
    Extracts upper and lower body color distributions for persons, and dominant color channels
    for vehicles to provide explainable cross-camera visual consistency without heavy deep learning overhead.
    """

    def __init__(self, h_bins: int = 16, s_bins: int = 8, v_bins: int = 8):
        self.h_bins = h_bins
        self.s_bins = s_bins
        self.v_bins = v_bins
        self.feature_dim = (h_bins + s_bins + v_bins) * 2  # 2 spatial vertical zones

    def extract_features(self, crop: Optional[np.ndarray], metadata: Optional[dict] = None) -> np.ndarray:
        """
        Extracts multi-zone HSV histograms from bounding box crop.
        If crop is unavailable (e.g. simulated observation), falls back to metadata feature vector or deterministic seed.
        """
        if metadata and "appearance_vector" in metadata and metadata["appearance_vector"] is not None:
            vec = np.array(metadata["appearance_vector"], dtype=np.float32)
            norm = np.linalg.norm(vec)
            return vec / (norm + 1e-6)

        if crop is None or crop.size == 0 or crop.shape[0] < 4 or crop.shape[1] < 4:
            # Return zero feature vector if no visual content
            return np.zeros(self.feature_dim, dtype=np.float32)

        try:
            hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
            h, w = hsv.shape[:2]
            mid_h = h // 2

            # Upper zone (torso / upper vehicle)
            upper = hsv[:mid_h, :]
            # Lower zone (legs / lower vehicle)
            lower = hsv[mid_h:, :]

            def compute_zone_hist(zone: np.ndarray) -> np.ndarray:
                if zone.size == 0:
                    return np.zeros(self.h_bins + self.s_bins + self.v_bins, dtype=np.float32)
                
                h_hist = cv2.calcHist([zone], [0], None, [self.h_bins], [0, 180])
                s_hist = cv2.calcHist([zone], [1], None, [self.s_bins], [0, 256])
                v_hist = cv2.calcHist([zone], [2], None, [self.v_bins], [0, 256])

                h_hist = cv2.normalize(h_hist, h_hist).flatten()
                s_hist = cv2.normalize(s_hist, s_hist).flatten()
                v_hist = cv2.normalize(v_hist, v_hist).flatten()
                return np.concatenate([h_hist, s_hist, v_hist])

            upper_feat = compute_zone_hist(upper)
            lower_feat = compute_zone_hist(lower)
            combined = np.concatenate([upper_feat, lower_feat])

            norm = np.linalg.norm(combined)
            return combined / (norm + 1e-6)

        except Exception:
            return np.zeros(self.feature_dim, dtype=np.float32)

    def compute_similarity(self, feat_a: np.ndarray, feat_b: np.ndarray) -> float:
        """
        Computes cosine similarity between normalized feature vectors.
        Returns a score bounded in [0.0, 1.0].
        """
        if feat_a is None or feat_b is None:
            return 0.0
        
        feat_a = np.asarray(feat_a, dtype=np.float32).flatten()
        feat_b = np.asarray(feat_b, dtype=np.float32).flatten()

        if len(feat_a) == 0 or len(feat_b) == 0:
            return 0.0

        # Equalize dimensions if needed
        if len(feat_a) != len(feat_b):
            min_len = min(len(feat_a), len(feat_b))
            feat_a = feat_a[:min_len]
            feat_b = feat_b[:min_len]

        norm_a = np.linalg.norm(feat_a)
        norm_b = np.linalg.norm(feat_b)

        if norm_a < 1e-6 or norm_b < 1e-6:
            return 0.0

        # Cosine dot product
        cosine = float(np.dot(feat_a, feat_b) / (norm_a * norm_b))
        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, (cosine + 1.0) / 2.0 if cosine < 0 else cosine))
