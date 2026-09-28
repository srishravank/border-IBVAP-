import time
import pytest
import numpy as np
from backend.health.camera_health import CameraHealthMonitor
from backend.models.camera import CameraStatus
from backend.models.event import CameraEvent, EventType


def test_camera_health_state_transitions():
    """Tests basic health state machine transitions."""
    events = []
    def on_event(evt: CameraEvent):
        events.append(evt)

    monitor = CameraHealthMonitor(camera_id="TEST-CAM-HEALTH", on_event_callback=on_event)
    assert monitor.current_status == CameraStatus.OFFLINE

    # Process first normal frame -> transitions to ONLINE
    frame1 = np.random.randint(50, 200, (720, 1280, 3), dtype=np.uint8)
    status = monitor.process_frame(frame1, frame_id=1)
    assert status == CameraStatus.ONLINE
    assert monitor.current_status == CameraStatus.ONLINE
    assert len(events) >= 1
    assert events[-1].event_type == EventType.CAMERA_ONLINE

    # Simulate disconnect
    monitor.record_disconnect("RTSP timeout")
    assert monitor.current_status == CameraStatus.OFFLINE
    assert events[-1].event_type == EventType.CAMERA_OFFLINE

    # Simulate reconnecting
    monitor.record_reconnecting("Retry #1")
    assert monitor.current_status == CameraStatus.RECONNECTING
    assert events[-1].event_type == EventType.CAMERA_RECONNECTING


def test_frozen_frame_detection():
    """Tests that identical static frames trigger FROZEN status after threshold seconds."""
    events = []
    monitor = CameraHealthMonitor(
        camera_id="TEST-FROZEN",
        on_event_callback=lambda e: events.append(e),
        frozen_seconds_threshold=0.5,  # Short threshold for test
        frozen_diff_threshold=1.0
    )

    # Static frame
    static_frame = np.ones((720, 1280, 3), dtype=np.uint8) * 120

    # First frame received
    monitor.process_frame(static_frame, frame_id=1)
    assert monitor.current_status == CameraStatus.ONLINE

    # Wait past threshold
    time.sleep(0.6)

    # Second identical frame
    status = monitor.process_frame(static_frame, frame_id=2)
    assert status == CameraStatus.FROZEN
    assert monitor.current_status == CameraStatus.FROZEN
    assert any(e.event_type == EventType.FRAME_FROZEN for e in events)

    # Now provide moving dynamic frame -> recovers to ONLINE
    dynamic_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    status2 = monitor.process_frame(dynamic_frame, frame_id=3)
    assert status2 == CameraStatus.ONLINE
    assert monitor.current_status == CameraStatus.ONLINE


def test_black_frame_detection():
    """Tests that empty/black frames trigger BLACK_FRAME status."""
    events = []
    monitor = CameraHealthMonitor(
        camera_id="TEST-BLACK",
        on_event_callback=lambda e: events.append(e),
        black_mean_threshold=5.0
    )

    # Pure black frame
    black_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    status = monitor.process_frame(black_frame, frame_id=1)
    
    assert status == CameraStatus.BLACK_FRAME
    assert monitor.current_status == CameraStatus.BLACK_FRAME
    assert any(e.event_type == EventType.INVALID_FRAME for e in events)
