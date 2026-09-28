import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.connection import init_db
from backend.services.simulation_engine import simulation_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_risk_api_endpoints():
    # Trigger simulation to populate DB
    demo_res = simulation_engine.run_multi_camera_journey_demo()
    subj_id = demo_res["subject_id"]
    inc_id = f"INC-{subj_id}"

    # 1. GET /api/incidents/{incident_id}/risk
    res_risk = client.get(f"/api/incidents/{inc_id}/risk")
    assert res_risk.status_code == 200
    risk_data = res_risk.json()
    assert risk_data["incident_id"] == inc_id
    assert "score" in risk_data
    assert "risk_level" in risk_data
    assert "explanation" in risk_data
    assert isinstance(risk_data["factors"], list)

    # 2. GET /api/incidents/{incident_id}/risk/history
    res_hist = client.get(f"/api/incidents/{inc_id}/risk/history")
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    assert len(hist_data) >= 1

    # 3. GET /api/incidents/{incident_id}/risk/factors
    res_factors = client.get(f"/api/incidents/{inc_id}/risk/factors")
    assert res_factors.status_code == 200
    factors_data = res_factors.json()
    assert len(factors_data) >= 1

    # 4. GET /api/risk/config
    res_cfg = client.get("/api/risk/config")
    assert res_cfg.status_code == 200
    cfg_data = res_cfg.json()
    assert "weights" in cfg_data

    # 5. PUT /api/risk/config
    res_put = client.put("/api/risk/config", json={
        "weights": {"zone": 25.0, "fence": 25.0, "night": 20.0, "trajectory": 10.0, "cross_camera": 10.0, "vehicle": 10.0, "behaviour": 0.0}
    })
    assert res_put.status_code == 200
    assert res_put.json()["weights"]["zone"] == 25.0

    # 6. GET /api/risk/summary
    res_sum = client.get("/api/risk/summary")
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert "total_incidents_assessed" in sum_data

    # 7. GET /api/incidents/{incident_id}/intelligence (Phase 6 Object)
    res_intel = client.get(f"/api/incidents/{inc_id}/intelligence")
    assert res_intel.status_code == 200
    intel_data = res_intel.json()
    assert intel_data["incident_id"] == inc_id
    assert "risk" in intel_data
    assert "context" in intel_data
    assert "timeline" in intel_data
    assert "journey" in intel_data
