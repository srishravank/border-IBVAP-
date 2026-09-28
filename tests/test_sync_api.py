import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.simulation_engine import simulation_engine
from backend.services.connectivity_service import connectivity_service
from backend.services.sync_service import sync_service
from backend.models.sync import ConnectionState

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_state():
    simulation_engine.reset_simulation()
    connectivity_service.set_state(ConnectionState.ONLINE, "API Test reset", is_simulated=False)
    yield
    simulation_engine.reset_simulation()
    connectivity_service.set_state(ConnectionState.ONLINE, "API Test cleanup", is_simulated=False)


def test_connectivity_api_endpoints():
    """Tests GET /api/system/connectivity and POST /api/system/connectivity/simulate."""
    # 1. Check initial connectivity status
    res = client.get("/api/system/connectivity")
    assert res.status_code == 200
    data = res.json()
    assert data["state"] == "ONLINE"
    assert "edge_id" in data

    # 2. Simulate Offline
    sim_res = client.post("/api/system/connectivity/simulate", json={
        "state": "OFFLINE",
        "reason": "Test disconnect"
    })
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["state"] == "OFFLINE"
    assert sim_data["is_simulated"] is True

    # 3. Restore Online
    rest_res = client.post("/api/system/connectivity/simulate", json={
        "state": "ONLINE",
        "reason": "Test restore"
    })
    assert rest_res.status_code == 200
    assert rest_res.json()["state"] == "ONLINE"


def test_sync_status_and_queue_api():
    """Tests GET /api/sync/status and GET /api/sync/queue."""
    # Enqueue a test item
    sync_service.enqueue_item("INCIDENT", "INC-API-001", {"title": "API test incident"}, priority=1)

    # 1. Get Sync Status
    res = client.get("/api/sync/status")
    assert res.status_code == 200
    data = res.json()
    assert "connectivity" in data
    assert "summary" in data
    assert data["summary"]["total_queued"] >= 1

    # 2. Get Queue Items
    q_res = client.get("/api/sync/queue")
    assert q_res.status_code == 200
    items = q_res.json()
    assert len(items) >= 1
    assert any(it["entity_id"] == "INC-API-001" for it in items)


def test_sync_trigger_and_retry_api():
    """Tests POST /api/sync/start and POST /api/sync/retry/{item_id}."""
    # Enqueue item while offline
    connectivity_service.simulate_offline("API Offline")
    item = sync_service.enqueue_item("EVENT", "EVT-API-001", {"data": 123}, priority=2)

    # Trigger Sync while online
    connectivity_service.restore_connection("Back online")
    sync_res = client.post("/api/sync/start")
    assert sync_res.status_code == 200
    assert sync_res.json()["status"] == "completed"

    # Retry item API
    retry_res = client.post(f"/api/sync/retry/{item.id}")
    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "success"


def test_central_sync_batch_api():
    """Tests POST /api/sync/batch central ingestion endpoint."""
    batch_payload = {
        "edge_id": "EDGE-TEST-01",
        "batch_id": "BATCH-API-001",
        "items": [
            {
                "edge_id": "EDGE-TEST-01",
                "idempotency_key": "EDGE-TEST-01-INC-001",
                "entity_type": "INCIDENT",
                "entity_id": "INC-001",
                "operation": "CREATE",
                "priority": 1,
                "created_at_edge": "2026-09-20T17:40:00Z",
                "payload": {"score": 90}
            }
        ],
        "sent_at": "2026-09-20T17:40:00Z"
    }

    # 1. Ingest batch
    res = client.post("/api/sync/batch", json=batch_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["accepted_count"] == 1
    assert data["duplicate_count"] == 0

    # 2. Resend same batch (Idempotency test)
    res_dup = client.post("/api/sync/batch", json=batch_payload)
    assert res_dup.status_code == 200
    data_dup = res_dup.json()
    assert data_dup["accepted_count"] == 0
    assert data_dup["duplicate_count"] == 1
    assert data_dup["receipts"][0]["status"] == "DUPLICATE_ACCEPTED"
