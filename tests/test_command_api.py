import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.connection import init_db
from backend.services.simulation_engine import simulation_engine


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    simulation_engine.reset_simulation()
    yield
    simulation_engine.reset_simulation()


client = TestClient(app)


def test_dashboard_summary_api():
    """Tests /api/dashboard/summary overview metrics."""
    # Seed an incident
    simulation_engine.run_scenario_5_high_risk_with_vehicle()

    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_cameras"] >= 4
    assert data["total_incidents"] >= 1
    assert data["active_incidents"] >= 1
    assert data["sectors_count"] == 4
    assert "timestamp" in data


def test_sector_risks_api():
    """Tests /api/sectors/risk calculation."""
    simulation_engine.run_scenario_3_confirmed_fence_crossing()

    response = client.get("/api/sectors/risk")
    assert response.status_code == 200
    sectors = response.json()
    assert len(sectors) == 4
    sector_b = next((s for s in sectors if s["sector_id"] == "SECTOR-B"), None)
    assert sector_b is not None
    assert sector_b["risk_level"] in ("HIGH", "CRITICAL")
    assert sector_b["has_active_intrusion"] is True


def test_alerts_api():
    """Tests /api/alerts returns actionable alerts for high-risk incidents."""
    simulation_engine.run_scenario_3_confirmed_fence_crossing()

    response = client.get("/api/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) >= 1
    assert alerts[0]["risk_level"] in ("HIGH", "CRITICAL")
    assert alerts[0]["camera_id"] == "CAM-02"


def test_recommended_cameras_api():
    """Tests /api/incidents/{id}/recommended-cameras returns grounded forward-route recommendations."""
    res = simulation_engine.run_scenario_4_multi_camera_traverse()
    incident_id = res["incident_id"]

    response = client.get(f"/api/incidents/{incident_id}/recommended-cameras")
    assert response.status_code == 200
    recs = response.json()
    assert len(recs) >= 1
    for r in recs:
        assert "camera_id" in r
        assert "reason" in r
        assert "relationship" in r


def test_incident_narrative_api():
    """Tests /api/incidents/{id}/narrative returns objective, neutral summary without speculation."""
    res = simulation_engine.run_scenario_5_high_risk_with_vehicle()
    incident_id = res["incident_id"]

    response = client.get(f"/api/incidents/{incident_id}/narrative")
    assert response.status_code == 200
    data = response.json()
    assert data["incident_id"] == incident_id
    assert len(data["key_facts"]) >= 2
    assert "subject" in data["narrative"].lower()
    # Confirm neutral language without hallucinated terms
    assert "criminal" not in data["narrative"].lower()
    assert "guilty" not in data["narrative"].lower()


def test_operator_lifecycle_api_endpoints():
    """Tests REST endpoints for acknowledge, investigate, close, and notes."""
    res = simulation_engine.run_scenario_3_confirmed_fence_crossing()
    incident_id = res["incident_id"]

    # 1. Acknowledge
    ack_res = client.post(
        f"/api/incidents/{incident_id}/acknowledge",
        json={"operator_id": "OP-101", "role": "OPERATOR", "action": "ACKNOWLEDGE", "notes": "Ack alarm"}
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["current_status"] == "ACKNOWLEDGED"

    # 2. Add note
    note_res = client.post(
        f"/api/incidents/{incident_id}/notes",
        json={"operator_id": "OP-101", "role": "OPERATOR", "note": "Checked perimeter fence section 4."}
    )
    assert note_res.status_code == 200
    assert note_res.json()["note"] == "Checked perimeter fence section 4."

    # 3. Investigate
    inv_res = client.post(
        f"/api/incidents/{incident_id}/investigate",
        json={"operator_id": "OP-102", "role": "INVESTIGATOR", "action": "INVESTIGATE"}
    )
    assert inv_res.status_code == 200
    assert inv_res.json()["current_status"] == "INVESTIGATING"

    # 4. Close
    close_res = client.post(
        f"/api/incidents/{incident_id}/close",
        json={"operator_id": "OP-103", "role": "SUPERVISOR", "action": "CLOSE", "notes": "Resolved"}
    )
    assert close_res.status_code == 200
    assert close_res.json()["current_status"] == "CLOSED"

    # 5. Retrieve notes & actions
    notes_get = client.get(f"/api/incidents/{incident_id}/notes")
    assert notes_get.status_code == 200
    assert len(notes_get.json()) >= 1

    actions_get = client.get(f"/api/incidents/{incident_id}/actions")
    assert actions_get.status_code == 200
    assert len(actions_get.json()) >= 3
