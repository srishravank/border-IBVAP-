import pytest
import numpy as np
from ai.tracking.bytetrack_tracker import ByteTrackTracker, STrack
from backend.models.detection import DetectionResult
from backend.models.track import TrackState


def test_bytetrack_track_id_persistence():
    """
    Test: Moving object receives persistent Track ID across successive frames.
    """
    STrack.reset_counter()
    tracker = ByteTrackTracker(camera_id="CAM-TEST", track_thresh=0.4, trajectory_history_length=15)

    # Frame 1: Person at (100, 100, 180, 260)
    det1 = [
        DetectionResult(
            class_name="person",
            object_type="person",
            subclass=None,
            confidence=0.92,
            bbox=[100.0, 100.0, 180.0, 260.0],
            center=[140.0, 180.0]
        )
    ]
    tracks_f1 = tracker.update(det1, frame_id=1)
    assert len(tracks_f1) == 1
    initial_id = tracks_f1[0].track_id
    assert tracks_f1[0].formatted_id == f"P{initial_id:03d}"

    # Frame 2: Same person moved slightly to (105, 103, 185, 263)
    det2 = [
        DetectionResult(
            class_name="person",
            object_type="person",
            subclass=None,
            confidence=0.90,
            bbox=[105.0, 103.0, 185.0, 263.0],
            center=[145.0, 183.0]
        )
    ]
    tracks_f2 = tracker.update(det2, frame_id=2)
    assert len(tracks_f2) == 1
    assert tracks_f2[0].track_id == initial_id, "Track ID must remain identical across consecutive frames"
    assert tracks_f2[0].formatted_id == f"P{initial_id:03d}"
    assert len(tracks_f2[0].trajectory) >= 2

    # Frame 3: Same person moved further to (110, 106, 190, 266)
    det3 = [
        DetectionResult(
            class_name="person",
            object_type="person",
            subclass=None,
            confidence=0.88,
            bbox=[110.0, 106.0, 190.0, 266.0],
            center=[150.0, 186.0]
        )
    ]
    tracks_f3 = tracker.update(det3, frame_id=3)
    assert len(tracks_f3) == 1
    assert tracks_f3[0].track_id == initial_id
    assert len(tracks_f3[0].trajectory) == 3


def test_bytetrack_multiple_simultaneous_objects():
    """
    Test: Tracker accurately maintains distinct persistent IDs for multiple simultaneous objects (Person + Car).
    """
    STrack.reset_counter()
    tracker = ByteTrackTracker(camera_id="CAM-TEST", track_thresh=0.35)

    # Frame 1: Person and Car
    dets_f1 = [
        DetectionResult(
            class_name="person",
            object_type="person",
            confidence=0.91,
            bbox=[50.0, 80.0, 120.0, 240.0],
            center=[85.0, 160.0]
        ),
        DetectionResult(
            class_name="car",
            object_type="vehicle",
            subclass="car",
            confidence=0.85,
            bbox=[500.0, 300.0, 750.0, 480.0],
            center=[625.0, 390.0]
        )
    ]
    tracks1 = tracker.update(dets_f1, frame_id=1)
    assert len(tracks1) == 2
    person_track = next(t for t in tracks1 if t.object_type == "person")
    vehicle_track = next(t for t in tracks1 if t.object_type == "vehicle")
    assert person_track.formatted_id.startswith("P")
    assert vehicle_track.formatted_id.startswith("V")
    assert person_track.track_id != vehicle_track.track_id

    # Frame 2: Both objects move
    dets_f2 = [
        DetectionResult(
            class_name="person",
            object_type="person",
            confidence=0.89,
            bbox=[55.0, 82.0, 125.0, 242.0],
            center=[90.0, 162.0]
        ),
        DetectionResult(
            class_name="car",
            object_type="vehicle",
            subclass="car",
            confidence=0.87,
            bbox=[520.0, 300.0, 770.0, 480.0],
            center=[645.0, 390.0]
        )
    ]
    tracks2 = tracker.update(dets_f2, frame_id=2)
    assert len(tracks2) == 2
    p2 = next(t for t in tracks2 if t.object_type == "person")
    v2 = next(t for t in tracks2 if t.object_type == "vehicle")
    assert p2.track_id == person_track.track_id
    assert v2.track_id == vehicle_track.track_id


def test_bytetrack_trajectory_history_bounded():
    """Test: Trajectory history is recorded and correctly bounded by trajectory_history_length."""
    STrack.reset_counter()
    tracker = ByteTrackTracker(camera_id="CAM-TEST", track_thresh=0.3, trajectory_history_length=5)

    for f_idx in range(1, 10):
        det = [
            DetectionResult(
                class_name="person",
                object_type="person",
                confidence=0.9,
                bbox=[100.0 + f_idx * 5, 100.0, 180.0 + f_idx * 5, 260.0],
                center=[140.0 + f_idx * 5, 180.0]
            )
        ]
        tracks = tracker.update(det, frame_id=f_idx)

    assert len(tracks) == 1
    assert len(tracks[0].trajectory) <= 5
