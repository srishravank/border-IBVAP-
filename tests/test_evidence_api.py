import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.simulation_engine import simulation_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_simulation():
    simulation_engine.reset_simulation()
    yield
    simulation_engine.reset_simulation()


def test_generate_and_get_evidence_api():
    """Tests POST /api/incidents/{incident_id}/evidence and GET /api/incidents/{incident_id}/evidence."""
    scenario_res = simulation_engine.run_scenario_5_high_risk_with_vehicle()
    incident_id = scenario_res["incident_id"]

    # 1. Generate evidence
    res = client.post(
        f"/api/incidents/{incident_id}/evidence",
        json={"operator_id": "OP-9402", "role": "OPERATOR", "version": "1.0", "notes": "API test package"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["incident_id"] == incident_id
    assert data["status"] == "ANCHORED"
    assert data["hash"]["algorithm"] == "SHA-256"
    assert data["anchor"]["transaction_id"].startswith("TX-")
    evidence_id = data["evidence_id"]

    # 2. Get list of packages for incident
    res_list = client.get(f"/api/incidents/{incident_id}/evidence")
    assert res_list.status_code == 200
    packages = res_list.json()
    assert len(packages) >= 1
    assert packages[0]["evidence_id"] == evidence_id


def test_get_evidence_manifest_and_anchor_api():
    """Tests GET /api/evidence/{evidence_id}/manifest and /api/evidence/{evidence_id}/anchor."""
    scenario_res = simulation_engine.run_scenario_4_multi_camera_traverse()
    incident_id = scenario_res["incident_id"]

    # Create evidence
    gen_res = client.post(f"/api/incidents/{incident_id}/evidence", json={"version": "1.0"})
    evidence_id = gen_res.json()["evidence_id"]

    # Manifest API
    res_manifest = client.get(f"/api/evidence/{evidence_id}/manifest")
    assert res_manifest.status_code == 200
    manifest = res_manifest.json()
    assert manifest["incident_id"] == incident_id
    assert "events" in manifest
    assert "risk_assessment" in manifest

    # Anchor API
    res_anchor = client.get(f"/api/evidence/{evidence_id}/anchor")
    assert res_anchor.status_code == 200
    anchor = res_anchor.json()
    assert anchor["evidence_id"] == evidence_id
    assert anchor["transaction_id"].startswith("TX-")
    assert anchor["block_number"] >= 1


def test_verify_evidence_api_and_tamper_demo_api():
    """Tests POST /api/evidence/{evidence_id}/verify, /tamper-demo, and /restore-demo."""
    scenario_res = simulation_engine.run_scenario_5_high_risk_with_vehicle()
    incident_id = scenario_res["incident_id"]

    # Create evidence
    gen_res = client.post(f"/api/incidents/{incident_id}/evidence", json={"version": "1.0"})
    evidence_id = gen_res.json()["evidence_id"]

    # 1. Verify -> AUTHENTIC
    res_v1 = client.post(f"/api/evidence/{evidence_id}/verify", json={"operator_id": "OP-9402", "role": "OPERATOR"})
    assert res_v1.status_code == 200
    v1_data = res_v1.json()
    assert v1_data["status"] == "AUTHENTIC"
    assert v1_data["is_authentic"] is True

    # 2. Tamper demo
    res_tamper = client.post(
        f"/api/evidence/{evidence_id}/tamper-demo",
        json={"tamper_field": "risk_score", "tamper_value": 99.5}
    )
    assert res_tamper.status_code == 200

    # 3. Verify -> TAMPERED
    res_v2 = client.post(f"/api/evidence/{evidence_id}/verify")
    assert res_v2.status_code == 200
    v2_data = res_v2.json()
    assert v2_data["status"] == "TAMPERED"
    assert v2_data["is_authentic"] is False

    # 4. Restore demo
    res_restore = client.post(f"/api/evidence/{evidence_id}/restore-demo")
    assert res_restore.status_code == 200

    # 5. Verify -> AUTHENTIC
    res_v3 = client.post(f"/api/evidence/{evidence_id}/verify")
    assert res_v3.status_code == 200
    assert res_v3.json()["status"] == "AUTHENTIC"


def test_ledger_blocks_api():
    """Tests GET /api/ledger/blocks."""
    res = client.get("/api/ledger/blocks")
    assert res.status_code == 200
    blocks = res.json()
    assert isinstance(blocks, list)
    assert len(blocks) >= 1
    assert blocks[-1]["block_number"] == 0  # Genesis block
