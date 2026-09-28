"""
Phase 11 Demo Readiness & Hero Scenario Automated Tests
Validates deterministic demo state machine, individual stage executions,
tamper-evidence demonstration, offline-sync demo cycle, federated learning stage,
full hero scenario automation, and demo reset capabilities.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.demo_controller import demo_controller, DemoStage

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_demo_state():
    """Ensure clean demo state before and after each test."""
    demo_controller.reset_demo()
    yield
    demo_controller.reset_demo()


def test_demo_status_endpoint():
    """Test GET /api/demo/status returns valid state machine payload."""
    response = client.get("/api/demo/status")
    assert response.status_code == 200
    data = response.json()
    assert "current_stage" in data
    assert "demo_mode" in data
    assert "total_cameras" in data
    assert "connectivity_state" in data
    assert data["current_stage"] == DemoStage.DEMO_IDLE


def test_demo_reset_endpoint():
    """Test POST /api/demo/reset resets execution state."""
    # Execute a step first
    demo_controller.execute_step("SEE")
    assert demo_controller.current_stage == DemoStage.CAMERAS_RUNNING

    response = client.post("/api/demo/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert demo_controller.current_stage == DemoStage.DEMO_IDLE


def test_demo_individual_step_execution():
    """Test POST /api/demo/step/{step_name} for sequential stages."""
    # Step 1: SEE
    r1 = client.post("/api/demo/step/1")
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["status"] == "SUCCESS"
    assert "SEE" in d1["step"]

    # Step 2: UNDERSTAND
    r2 = client.post("/api/demo/step/2")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["status"] == "SUCCESS"
    assert "UNDERSTAND" in d2["step"]

    # Step 3: VERIFY
    r3 = client.post("/api/demo/step/3")
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["status"] == "SUCCESS"

    # Step 4: SUPPRESS
    r4 = client.post("/api/demo/step/4")
    assert r4.status_code == 200
    d4 = r4.json()
    assert d4["status"] == "SUCCESS"


def test_demo_evidence_tamper_restore_cycle():
    """Test steps 8 (PROVE), 9 (TAMPER), 10 (RESTORE)."""
    # Step 8: PROVE
    r_prove = client.post("/api/demo/step/8")
    assert r_prove.status_code == 200
    d_prove = r_prove.json()
    assert d_prove["status"] == "SUCCESS"
    assert "evidence_id" in d_prove

    ev_id = d_prove["evidence_id"]

    # Step 9: TAMPER
    r_tamper = client.post("/api/demo/step/9")
    assert r_tamper.status_code == 200
    d_tamper = r_tamper.json()
    assert d_tamper["status"] == "SUCCESS"
    assert d_tamper["tamper_detected"] is True

    # Step 10: RESTORE
    r_restore = client.post("/api/demo/step/10")
    assert r_restore.status_code == 200
    d_restore = r_restore.json()
    assert d_restore["status"] == "SUCCESS"
    assert d_restore["is_authentic"] is True


def test_demo_offline_sync_cycle():
    """Test steps 11 (OFFLINE) and 12 (SYNC)."""
    # Step 11: OFFLINE
    r_off = client.post("/api/demo/step/11")
    assert r_off.status_code == 200
    d_off = r_off.json()
    assert d_off["status"] == "SUCCESS"
    assert d_off["connectivity_state"] == "OFFLINE"

    # Step 12: SYNC
    r_sync = client.post("/api/demo/step/12")
    assert r_sync.status_code == 200
    d_sync = r_sync.json()
    assert d_sync["status"] == "SUCCESS"
    assert d_sync["connectivity_state"] == "ONLINE"


def test_demo_learn_stage():
    """Test step 13 (LEARN)."""
    r_learn = client.post("/api/demo/step/13")
    assert r_learn.status_code == 200
    d_learn = r_learn.json()
    assert d_learn["status"] == "SUCCESS"
    assert "learning_summary" in d_learn


def test_demo_hero_scenario_full_run():
    """Test POST /api/demo/hero-scenario executes full deterministic pipeline."""
    response = client.post("/api/demo/hero-scenario")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "pipeline_summary" in data


def test_demo_invalid_step_handling():
    """Test executing invalid step returns 400."""
    response = client.post("/api/demo/step/invalid_step_999")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
