import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

from backend.config import settings
from ai.schemas.observation import AIObservation
from backend.models.security_event import EventStatus, VerificationDetail


class CandidateVerificationTracker:
    """
    Manages multi-frame temporal consistency and confirmation for a candidate security event.
    Requires `required_frames` supporting detections within a `window_frames` window before promoting to CONFIRMED.
    """

    def __init__(
        self,
        candidate_key: str,
        camera_id: str,
        track_id: int,
        zone_id: str,
        event_type: str,
        required_frames: int = settings.VERIFICATION_REQUIRED_FRAMES,
        window_frames: int = settings.VERIFICATION_WINDOW_FRAMES,
        max_age_frames: int = settings.MAX_CANDIDATE_AGE_FRAMES
    ):
        self.candidate_key = candidate_key
        self.camera_id = camera_id
        self.track_id = track_id
        self.zone_id = zone_id
        self.event_type = event_type
        
        self.required_frames = required_frames
        self.window_frames = window_frames
        self.max_age_frames = max_age_frames

        self.status = EventStatus.CANDIDATE
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.confirmed_at: Optional[str] = None
        
        self.start_frame_id: int = 0
        self.last_frame_id: int = 0
        self.supporting_frame_ids: List[int] = []
        self.confidences: List[float] = []
        self.suppression_reasons: List[str] = []
        self.latest_observation: Optional[AIObservation] = None

    def add_observation(self, obs: AIObservation, is_valid_suppression: bool = True, reasons: Optional[List[str]] = None) -> Tuple[EventStatus, VerificationDetail]:
        """
        Ingests a new supporting observation for this candidate event.
        Updates verification counts and transitions state (CANDIDATE -> VERIFYING -> CONFIRMED / REJECTED).
        """
        frame_id = obs.frame_id
        self.latest_observation = obs
        self.last_frame_id = frame_id

        if not self.start_frame_id:
            self.start_frame_id = frame_id

        # If suppression filters failed
        if not is_valid_suppression:
            if reasons:
                self.suppression_reasons.extend(reasons)
            # If rejected immediately on first attempt or disqualified
            if len(self.supporting_frame_ids) == 0:
                self.status = EventStatus.REJECTED

            return self.status, self.get_verification_detail()

        # Record valid supporting frame
        if frame_id not in self.supporting_frame_ids:
            self.supporting_frame_ids.append(frame_id)
            self.confidences.append(obs.object.confidence)

        confirmed_count = len(self.supporting_frame_ids)
        frame_span = frame_id - self.start_frame_id + 1

        # Check if confirmed threshold is reached within acceptable temporal window
        if confirmed_count >= self.required_frames and frame_span <= self.window_frames:
            self.status = EventStatus.CONFIRMED
            self.confirmed_at = datetime.now(timezone.utc).isoformat()
        elif confirmed_count > 1:
            self.status = EventStatus.VERIFYING
        else:
            self.status = EventStatus.CANDIDATE

        # Check if frame span exceeded without reaching threshold
        if frame_span > self.window_frames and confirmed_count < self.required_frames:
            self.status = EventStatus.EXPIRED

        return self.status, self.get_verification_detail()

    def check_timeout(self, current_frame_id: int) -> bool:
        """Checks if candidate has expired due to lack of subsequent frames."""
        if self.status in (EventStatus.CANDIDATE, EventStatus.VERIFYING):
            if (current_frame_id - self.last_frame_id) > (self.window_frames + 2):
                self.status = EventStatus.EXPIRED
                return True
        return False

    def get_verification_detail(self) -> VerificationDetail:
        avg_conf = sum(self.confidences) / len(self.confidences) if self.confidences else 0.0
        v_status = "PASSED" if self.status == EventStatus.CONFIRMED else ("FAILED" if self.status in (EventStatus.REJECTED, EventStatus.EXPIRED) else "PENDING")

        return VerificationDetail(
            required_frames=self.required_frames,
            confirmed_frames=len(self.supporting_frame_ids),
            verification_status=v_status,
            supporting_frame_ids=list(self.supporting_frame_ids),
            average_confidence=round(avg_conf, 3),
            suppression_reasons=list(set(self.suppression_reasons))
        )
