from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

from backend.config import settings
from ai.schemas.observation import AIObservation
from backend.models.track import TrackedObject
from backend.models.camera import CameraStatus


class BaseFalsePositiveFilter(ABC):
    """Abstract Base Class for False-Positive Suppression Filters."""

    @abstractmethod
    def evaluate(
        self,
        observation: AIObservation,
        camera_status: CameraStatus = CameraStatus.ONLINE,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Returns:
            Tuple[bool, Optional[str]]: (passed, rejection_reason)
        """
        pass


class TrackPersistenceFilter(BaseFalsePositiveFilter):
    """
    Suppresses transient single-frame detections (foliage flicker, dust, laser glare).
    Requires a tracked target to persist for at least `min_track_age` frames.
    """

    def __init__(self, min_track_age: int = settings.MIN_TRACK_AGE_FRAMES):
        self.min_track_age = min_track_age

    def evaluate(
        self,
        observation: AIObservation,
        camera_status: CameraStatus = CameraStatus.ONLINE,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        # Check trajectory length or age in extra context
        traj_len = len(observation.trajectory)
        if traj_len < self.min_track_age:
            return False, f"Track age ({traj_len} frames) < minimum persistence ({self.min_track_age} frames)"
        return True, None


class SpatialConsistencyFilter(BaseFalsePositiveFilter):
    """
    Suppresses sudden sensor noise and teleporting detections by verifying spatial trajectory continuity.
    """

    def __init__(self, max_displacement_px: float = settings.SPATIAL_MAX_DISPLACEMENT_PX):
        self.max_displacement_px = max_displacement_px

    def evaluate(
        self,
        observation: AIObservation,
        camera_status: CameraStatus = CameraStatus.ONLINE,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        traj = observation.trajectory
        if len(traj) >= 2:
            p1 = np.array(traj[-2], dtype=np.float32)
            p2 = np.array(traj[-1], dtype=np.float32)
            displacement = float(np.linalg.norm(p2 - p1))
            if displacement > self.max_displacement_px:
                return False, f"Unrealistic spatial jump ({displacement:.1f}px > {self.max_displacement_px}px max)"
        return True, None


class ConfidenceFilter(BaseFalsePositiveFilter):
    """
    Suppresses detections that do not meet the minimum verification confidence threshold.
    """

    def __init__(self, min_confidence: float = settings.MIN_TRACK_CONFIDENCE):
        self.min_confidence = min_confidence

    def evaluate(
        self,
        observation: AIObservation,
        camera_status: CameraStatus = CameraStatus.ONLINE,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        if observation.object.confidence < self.min_confidence:
            return False, f"Detection confidence ({observation.object.confidence:.2f}) < threshold ({self.min_confidence:.2f})"
        return True, None


class CameraHealthFilter(BaseFalsePositiveFilter):
    """
    Suppresses security alerts if the CCTV source is suffering from severe health anomalies
    (e.g. lens covered, frozen stream, camera offline).
    """

    def evaluate(
        self,
        observation: AIObservation,
        camera_status: CameraStatus = CameraStatus.ONLINE,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        if camera_status != CameraStatus.ONLINE:
            return False, f"Suppressed due to camera health anomaly: {camera_status.value}"
        return True, None


class ObjectClassFilter(BaseFalsePositiveFilter):
    """
    Ensures that only target security categories (person, vehicle) trigger intrusion events.
    """

    def __init__(self, allowed_types: Optional[List[str]] = None):
        self.allowed_types = set(allowed_types or ["person", "vehicle"])

    def evaluate(
        self,
        observation: AIObservation,
        camera_status: CameraStatus = CameraStatus.ONLINE,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        obj_type = observation.object.type.lower()
        if obj_type not in self.allowed_types:
            return False, f"Non-target object type '{obj_type}' ignored"
        return True, None


class CompositeFalsePositiveFilter(BaseFalsePositiveFilter):
    """
    Orchestrates all active suppression filters and collects diagnostic feedback.
    """

    def __init__(self, filters: Optional[List[BaseFalsePositiveFilter]] = None):
        self.filters: List[BaseFalsePositiveFilter] = filters or [
            CameraHealthFilter(),
            ObjectClassFilter(),
            ConfidenceFilter(),
            TrackPersistenceFilter(),
            SpatialConsistencyFilter()
        ]

    def evaluate(
        self,
        observation: AIObservation,
        camera_status: CameraStatus = CameraStatus.ONLINE,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str]]:
        rejection_reasons = []
        for f in self.filters:
            passed, reason = f.evaluate(observation, camera_status, extra_context)
            if not passed and reason:
                rejection_reasons.append(reason)

        is_valid = len(rejection_reasons) == 0
        return is_valid, rejection_reasons
