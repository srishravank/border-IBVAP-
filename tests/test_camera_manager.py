import time
import pytest
from backend.services.camera_manager import CameraManager
from backend.database.models import CameraModel
from backend.models.frame import FramePacket
from backend.models.camera import CameraStatus


def test_multi_camera_independent_ingestion():
    """
    Test: 4 cameras (CAM-01 to CAM-04) ingest simultaneously in independent threads.
    Validates frame metadata (camera_id, timestamp, monotonic frame_id).
    """
    manager = CameraManager()
    
    received_packets = {"CAM-01": [], "CAM-02": [], "CAM-03": [], "CAM-04": []}
    
    def frame_hook(packet: FramePacket):
        if packet.metadata.camera_id in received_packets:
            received_packets[packet.metadata.camera_id].append(packet)

    manager.register_frame_hook(frame_hook)

    # Setup 4 camera models
    cameras = [
        CameraModel(camera_id="CAM-01", camera_name="Gate", location="Sec A", source_type="file", source="data/videos/camera01.mp4", enabled=True, target_fps=30.0),
        CameraModel(camera_id="CAM-02", camera_name="Fence", location="Sec B", source_type="file", source="data/videos/camera02.mp4", enabled=True, target_fps=30.0),
        CameraModel(camera_id="CAM-03", camera_name="River", location="Sec C", source_type="file", source="data/videos/camera03.mp4", enabled=True, target_fps=30.0),
        CameraModel(camera_id="CAM-04", camera_name="Tower", location="Sec D", source_type="file", source="data/videos/camera04.mp4", enabled=True, target_fps=30.0),
    ]

    for cam in cameras:
        manager.add_camera_worker(cam, start_immediately=True)

    # Let them ingest for 1.5 seconds
    time.sleep(1.5)

    try:
        for cam_id in ["CAM-01", "CAM-02", "CAM-03", "CAM-04"]:
            pkts = received_packets[cam_id]
            assert len(pkts) > 5, f"{cam_id} should have received multiple frames"
            
            # Verify frame metadata
            sample = pkts[-1]
            assert sample.metadata.camera_id == cam_id
            assert sample.metadata.frame_id > 0
            assert sample.metadata.timestamp is not None
            assert sample.metadata.width == 1280
            assert sample.metadata.height == 720
            assert sample.frame is not None
            assert sample.frame.shape == (720, 1280, 3)

            # Verify worker health status is ONLINE
            status_resp = manager.get_camera_status(cam_id)
            assert status_resp.status == CameraStatus.ONLINE
            assert status_resp.fps > 0

    finally:
        manager.shutdown_all()


def test_camera_fault_isolation():
    """
    Test: Deliberately breaking CAM-03 stream must NOT interrupt CAM-01, CAM-02, CAM-04.
    """
    manager = CameraManager()
    
    cameras = [
        CameraModel(camera_id="CAM-01", camera_name="Gate", location="Sec A", source_type="file", source="data/videos/camera01.mp4", enabled=True, target_fps=25.0),
        CameraModel(camera_id="CAM-02", camera_name="Fence", location="Sec B", source_type="file", source="data/videos/camera02.mp4", enabled=True, target_fps=25.0),
        # CAM-03 has invalid path -> will fail
        CameraModel(camera_id="CAM-03", camera_name="Broken", location="Sec C", source_type="file", source="data/videos/broken_non_existent.mp4", enabled=True, target_fps=25.0),
        CameraModel(camera_id="CAM-04", camera_name="Tower", location="Sec D", source_type="file", source="data/videos/camera04.mp4", enabled=True, target_fps=25.0),
    ]

    for cam in cameras:
        manager.add_camera_worker(cam, start_immediately=True)

    time.sleep(1.5)

    try:
        # CAM-01, CAM-02, CAM-04 must be ONLINE
        assert manager.workers["CAM-01"].health_monitor.current_status == CameraStatus.ONLINE
        assert manager.workers["CAM-02"].health_monitor.current_status == CameraStatus.ONLINE
        assert manager.workers["CAM-04"].health_monitor.current_status == CameraStatus.ONLINE
        
        # CAM-03 must be OFFLINE or RECONNECTING without crashing the application
        c3_status = manager.workers["CAM-03"].health_monitor.current_status
        assert c3_status in (CameraStatus.OFFLINE, CameraStatus.RECONNECTING)
    finally:
        manager.shutdown_all()
