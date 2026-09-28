import time
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.zone_engine import zone_engine
from backend.services.event_manager import event_manager
from backend.models.zone import ZoneCreate, ZoneType


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        time.sleep(0.5)
        yield c


def test_zone_crud_api(client: TestClient):
    """Test: Create, read, update, and delete virtual fence zones via REST API."""
    # 1. Create new zone
    new_zone = {
        "camera_id": "CAM-01",
        "zone_name": "API Test Perimeter Zone",
        "zone_type": "restricted",
        "polygon": [[150.0, 150.0], [450.0, 150.0], [450.0, 450.0], [150.0, 450.0]],
        "enabled": True,
        "sensitivity": "high",
        "description": "Created during automated API testing",
        "color": "#F43F5E"
    }
    create_resp = client.post("/api/cameras/CAM-01/zones", json=new_zone)
    assert create_resp.status_code == 201
    zone_data = create_resp.json()
    zone_id = zone_data["zone_id"]
    assert zone_data["camera_id"] == "CAM-01"
    assert len(zone_data["polygon"]) == 4

    # 2. Get camera zones
    list_resp = client.get("/api/cameras/CAM-01/zones")
    assert list_resp.status_code == 200
    zones = list_resp.json()
    assert any(z["zone_id"] == zone_id for z in zones)

    # 3. Get single zone
    get_resp = client.get(f"/api/zones/{zone_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["zone_name"] == "API Test Perimeter Zone"

    # 4. Update zone
    upd_resp = client.put(f"/api/zones/{zone_id}", json={"zone_name": "Renamed Test Zone", "enabled": False})
    assert upd_resp.status_code == 200
    assert upd_resp.json()["zone_name"] == "Renamed Test Zone"
    assert upd_resp.json()["enabled"] is False

    # 5. Delete zone
    del_resp = client.delete(f"/api/zones/{zone_id}")
    assert del_resp.status_code == 200

    # 6. Verify 404 on deleted
    verify_resp = client.get(f"/api/zones/{zone_id}")
    assert verify_resp.status_code == 404


def test_security_events_api(client: TestClient):
    """Test: Query security events, candidate streams, and acknowledge incidents."""
    # Query all events
    events_resp = client.get("/api/events")
    assert events_resp.status_code == 200
    assert isinstance(events_resp.json(), list)

    # Query active candidates
    cands_resp = client.get("/api/events/candidates")
    assert cands_resp.status_code == 200
    assert isinstance(cands_resp.json(), list)
