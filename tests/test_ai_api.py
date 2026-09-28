import time
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.camera_manager import camera_manager
from backend.services.ai_pipeline import ai_service


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        # Give ingestion & AI half a second to capture and process frames
        time.sleep(0.8)
        yield c


def test_ai_global_status_api(client: TestClient):
    """Test: /api/ai/status returns model info, tracking algorithm, and active pipelines."""
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_name" in data
    assert data["tracking_algorithm"] == "ByteTrack"
    assert "active_camera_pipelines" in data


def test_camera_ai_detections_and_tracks_api(client: TestClient):
    """Test: AI detection, track query, and performance endpoints for CAM-01."""
    # Performance endpoint
    perf_resp = client.get("/api/cameras/CAM-01/performance")
    assert perf_resp.status_code == 200
    perf = perf_resp.json()
    assert "camera_id" in perf
    assert "inference_fps" in perf
    assert "total_pipeline_ms" in perf

    # Detections endpoint
    det_resp = client.get("/api/cameras/CAM-01/detections")
    assert det_resp.status_code == 200
    assert isinstance(det_resp.json(), list)

    # Tracks endpoint
    tracks_resp = client.get("/api/cameras/CAM-01/tracks")
    assert tracks_resp.status_code == 200
    assert isinstance(tracks_resp.json(), list)

    # Observations endpoint (Phase 3 format)
    obs_resp = client.get("/api/cameras/CAM-01/observations?limit=10")
    assert obs_resp.status_code == 200
    obs_list = obs_resp.json()
    assert isinstance(obs_list, list)
    if len(obs_list) > 0:
        obs = obs_list[0]
        assert "observation_id" in obs
        assert "camera_id" in obs
        assert "object" in obs
        assert "trajectory" in obs
