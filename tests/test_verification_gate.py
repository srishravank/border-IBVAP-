import pytest
from verification.temporal_gate import CandidateVerificationTracker
from backend.models.security_event import EventStatus
from ai.schemas.observation import AIObservation, ObservedObjectSummary


def make_sample_observation(frame_id: int, track_id: int = 17, confidence: float = 0.90) -> AIObservation:
    return AIObservation(
        observation_id=f"OBS-TEST-{frame_id}",
        camera_id="CAM-01",
        frame_id=frame_id,
        object=ObservedObjectSummary(
            track_id=track_id,
            formatted_id=f"P{track_id:03d}",
            type="person",
            class_name="person",
            confidence=confidence,
            bbox=[120.0, 100.0, 200.0, 300.0],
            center=[160.0, 200.0]
        ),
        trajectory=[[160.0, 190.0], [160.0, 200.0]]
    )


def test_multi_frame_verification_promotion():
    """
    Test: Candidate event transitions:
    Frame 1: CANDIDATE (1/3)
    Frame 2: VERIFYING (2/3)
    Frame 3: CONFIRMED (3/3)
    """
    tracker = CandidateVerificationTracker(
        candidate_key="CAM-01:17:ZONE-01:ZONE_INTRUSION",
        camera_id="CAM-01",
        track_id=17,
        zone_id="ZONE-01",
        event_type="ZONE_INTRUSION",
        required_frames=3,
        window_frames=5
    )

    # Frame 100 -> Candidate
    s1, v1 = tracker.add_observation(make_sample_observation(frame_id=100))
    assert s1 == EventStatus.CANDIDATE
    assert v1.confirmed_frames == 1
    assert v1.verification_status == "PENDING"

    # Frame 101 -> Verifying
    s2, v2 = tracker.add_observation(make_sample_observation(frame_id=101))
    assert s2 == EventStatus.VERIFYING
    assert v2.confirmed_frames == 2
    assert v2.verification_status == "PENDING"

    # Frame 102 -> Confirmed!
    s3, v3 = tracker.add_observation(make_sample_observation(frame_id=102))
    assert s3 == EventStatus.CONFIRMED
    assert v3.confirmed_frames == 3
    assert v3.verification_status == "PASSED"
    assert tracker.confirmed_at is not None


def test_single_frame_false_positive_timeout():
    """
    Test: Single frame detection that disappears is expired by the temporal gate without confirmation.
    """
    tracker = CandidateVerificationTracker(
        candidate_key="CAM-01:99:ZONE-01:ZONE_INTRUSION",
        camera_id="CAM-01",
        track_id=99,
        zone_id="ZONE-01",
        event_type="ZONE_INTRUSION",
        required_frames=3,
        window_frames=5
    )

    # Frame 100 -> Single detection
    s1, v1 = tracker.add_observation(make_sample_observation(frame_id=100, track_id=99))
    assert s1 == EventStatus.CANDIDATE

    # Target disappears (no frames 101, 102, 103, 104, 105, 106, 107, 108)
    expired = tracker.check_timeout(current_frame_id=108)
    assert expired is True
    assert tracker.status == EventStatus.EXPIRED
    assert tracker.get_verification_detail().verification_status == "FAILED"
