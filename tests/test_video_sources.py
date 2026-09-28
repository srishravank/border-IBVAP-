import os
import pytest
import numpy as np
from pathlib import Path
from backend.services.file_source import FileSource
from backend.services.webcam_source import WebcamSource
from backend.services.rtsp_source import RTSPSource


def test_valid_video_file_ingestion():
    """Test 1: Valid video file can connect and read frames with valid dimensions."""
    sample_file = "data/videos/camera01.mp4"
    assert os.path.exists(sample_file), "Sample video camera01.mp4 must exist"

    source = FileSource(camera_id="TEST-FILE-01", file_path=sample_file, loop=True, target_fps=30.0)
    assert source.connect() is True
    assert source.is_connected() is True

    ret, frame = source.read_frame()
    assert ret is True
    assert frame is not None
    assert isinstance(frame, np.ndarray)
    assert frame.shape[0] == 720
    assert frame.shape[1] == 1280
    assert frame.shape[2] == 3

    meta = source.get_metadata()
    assert meta["camera_id"] == "TEST-FILE-01"
    assert meta["width"] == 1280
    assert meta["height"] == 720
    assert meta["is_connected"] is True

    source.release()
    assert source.is_connected() is False


def test_invalid_video_path_handling():
    """Test 2: Invalid video file path fails gracefully without crashing."""
    source = FileSource(camera_id="TEST-INVALID-01", file_path="data/videos/non_existent_stream.mp4")
    assert source.connect() is False
    assert source.is_connected() is False

    ret, frame = source.read_frame()
    assert ret is False
    assert frame is None
    source.release()


def test_webcam_input_fallback():
    """Test 3: Webcam input initializes and handles absent hardware gracefully."""
    # Test with index 99 which simulates no webcam hardware
    source = WebcamSource(camera_id="TEST-WEBCAM-01", device_index=99)
    # connect() should return False gracefully rather than crashing
    connected = source.connect()
    if not connected:
        assert source.is_connected() is False
        ret, frame = source.read_frame()
        assert ret is False
        assert frame is None
    source.release()


def test_rtsp_connection_failure_handling():
    """Test 4: RTSP connection failure to unreachable IP does not crash and reports disconnected."""
    source = RTSPSource(
        camera_id="TEST-RTSP-01",
        rtsp_url="rtsp://fake_user:fake_pass@127.0.0.1:59999/live/stream"
    )
    connected = source.connect()
    assert connected is False
    assert source.is_connected() is False

    ret, frame = source.read_frame()
    assert ret is False
    assert frame is None
    source.release()
