import time
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.camera_manager import camera_manager


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_system_health_endpoint(client: TestClient):
    """Test: /api/health returns overall system ingestion metrics."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "metrics" in data
    assert "total_cameras" in data["metrics"]


def test_camera_crud_and_lifecycle_api(client: TestClient):
    """Test: Camera registration, status retrieval, start/stop, and deletion via REST API."""
    # Pre-cleanup in case of previous run
    client.delete("/api/cameras/CAM-TEST-API")

    # 1. Register new camera
    new_cam = {
        "camera_id": "CAM-TEST-API",
        "camera_name": "API Test Camera",
        "location": "Sector X",
        "source_type": "file",
        "source": "data/videos/camera01.mp4",
        "enabled": True,
        "target_fps": 25.0,
        "frame_width": 1280,
        "frame_height": 720,
        "description": "Created during automated API test"
    }
    create_resp = client.post("/api/cameras", json=new_cam)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["camera_id"] == "CAM-TEST-API"

    # Give worker half a second to capture
    time.sleep(0.6)

    # 2. Get camera list
    list_resp = client.get("/api/cameras")
    assert list_resp.status_code == 200
    cams = list_resp.json()
    assert any(c["camera_id"] == "CAM-TEST-API" for c in cams)

    # 3. Get single camera status
    status_resp = client.get("/api/cameras/CAM-TEST-API/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["camera_id"] == "CAM-TEST-API"
    assert status_data["is_ingesting"] is True

    # 4. Get camera snapshot
    snap_resp = client.get("/api/cameras/CAM-TEST-API/snapshot")
    assert snap_resp.status_code == 200
    assert snap_resp.headers["content-type"] == "image/jpeg"
    assert len(snap_resp.content) > 100

    # 5. Stop camera
    stop_resp = client.post("/api/cameras/CAM-TEST-API/stop")
    assert stop_resp.status_code == 200

    # 6. Start camera
    start_resp = client.post("/api/cameras/CAM-TEST-API/start")
    assert start_resp.status_code == 200

    # 7. Update camera
    update_payload = {"camera_name": "Renamed API Camera"}
    update_resp = client.put("/api/cameras/CAM-TEST-API", json=update_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["camera_name"] == "Renamed API Camera"

    # 8. Get events
    events_resp = client.get("/api/cameras/CAM-TEST-API/events")
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert isinstance(events, list)

    # 9. Delete camera
    del_resp = client.delete("/api/cameras/CAM-TEST-API")
    assert del_resp.status_code == 200

    # 10. Verify deletion
    verify_resp = client.get("/api/cameras/CAM-TEST-API")
    assert verify_resp.status_code == 404
