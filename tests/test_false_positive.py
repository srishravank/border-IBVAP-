import pytest
from verification.false_positive_filter import (
    TrackPersistenceFilter,
    SpatialConsistencyFilter,
    ConfidenceFilter,
    CameraHealthFilter,
    ObjectClassFilter,
    CompositeFalsePositiveFilter
)
from backend.models.camera import CameraStatus
from ai.schemas.observation import AIObservation, ObservedObjectSummary


def make_obs(
    track_age: int = 3,
    confidence: float = 0.85,
    object_type: str = "person",
    displacement_px: float = 20.0
) -> AIObservation:
    traj = [[100.0, 100.0]]
    for i in range(1, track_age):
        traj.append([100.0 + i * (displacement_px / max(1, track_age)), 100.0])

    return AIObservation(
        observation_id="OBS-FP-TEST",
        camera_id="CAM-01",
        frame_id=10,
        object=ObservedObjectSummary(
            track_id=1,
            formatted_id="P001",
            type=object_type,
            class_name=object_type,
            confidence=confidence,
            bbox=[100.0, 100.0, 180.0, 260.0],
            center=[140.0, 180.0]
        ),
        trajectory=traj
    )


def test_track_persistence_filter():
    """Test: Rejects detections with age < 2 frames."""
    f = TrackPersistenceFilter(min_track_age=2)
    obs_single = make_obs(track_age=1)
    passed, reason = f.evaluate(obs_single)
    assert passed is False
    assert "minimum persistence" in reason

    obs_persistent = make_obs(track_age=3)
    passed, reason = f.evaluate(obs_persistent)
    assert passed is True


def test_spatial_consistency_filter():
    """Test: Rejects sudden unrealistic spatial jumps (> 250px displacement)."""
    f = SpatialConsistencyFilter(max_displacement_px=250.0)
    
    # Large jump of 400px between consecutive frames
    obs_jump = AIObservation(
        observation_id="OBS-JUMP",
        camera_id="CAM-01",
        frame_id=2,
        object=ObservedObjectSummary(
            track_id=1,
            formatted_id="P001",
            type="person",
            class_name="person",
            confidence=0.9,
            bbox=[500.0, 500.0, 580.0, 660.0],
            center=[540.0, 580.0]
        ),
        trajectory=[[100.0, 100.0], [500.0, 500.0]]
    )
    passed, reason = f.evaluate(obs_jump)
    assert passed is False
    assert "spatial jump" in reason


def test_camera_health_isolation_filter():
    """Test: Suppresses intrusion events if camera is currently FROZEN, BLACK_FRAME, or OFFLINE."""
    f = CameraHealthFilter()
    obs = make_obs()

    # Normal ONLINE camera -> passed
    p1, _ = f.evaluate(obs, camera_status=CameraStatus.ONLINE)
    assert p1 is True

    # FROZEN camera -> suppressed
    p2, r2 = f.evaluate(obs, camera_status=CameraStatus.FROZEN)
    assert p2 is False
    assert "health anomaly" in r2

    # OFFLINE camera -> suppressed
    p3, r3 = f.evaluate(obs, camera_status=CameraStatus.OFFLINE)
    assert p3 is False


def test_confidence_filter():
    """Test: Rejects low-confidence detections below threshold."""
    f = ConfidenceFilter(min_confidence=0.40)
    obs_low = make_obs(confidence=0.30)
    passed, reason = f.evaluate(obs_low)
    assert passed is False
    assert "threshold" in reason
