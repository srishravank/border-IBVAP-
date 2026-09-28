import time
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.simulation_engine import simulation_engine

client = TestClient(app)


def test_models_api_endpoints():
    """Tests GET /api/models, /api/models/active, /api/models/{model_id}."""
    simulation_engine.reset_simulation()

    # GET active model
    res = client.get("/api/models/active")
    assert res.status_code == 200
    data = res.json()
    assert data["version"] == "1.0.0"
    assert data["status"] == "ACTIVE"
    assert len(data["model_hash"]) == 64

    # GET list models
    res_list = client.get("/api/models")
    assert res_list.status_code == 200
    models = res_list.json()
    assert len(models) >= 1

    # GET specific model
    res_detail = client.get(f"/api/models/{data['model_id']}")
    assert res_detail.status_code == 200
    assert res_detail.json()["model_id"] == data["model_id"]


def test_training_samples_and_review_api():
    """Tests GET /api/training/samples and POST review/relabel actions."""
    simulation_engine.reset_simulation()

    # List samples
    res = client.get("/api/training/samples")
    assert res.status_code == 200
    samples = res.json()
    assert len(samples) > 0

    pending = [s for s in samples if s["validation_status"] == "PENDING"]
    if pending:
        sample_id = pending[0]["sample_id"]
        # Approve sample
        res_app = client.post(
            f"/api/training/samples/{sample_id}/approve",
            json={"action": "APPROVE", "operator_id": "OP-9402", "role": "OPERATOR"}
        )
        assert res_app.status_code == 200
        assert res_app.json()["validation_status"] == "VALIDATED"


def test_local_training_and_federated_round_api():
    """Tests POST /api/training/start, GET /api/training/status, POST /api/federated/rounds."""
    simulation_engine.reset_simulation()

    # Training Status
    res_st = client.get("/api/training/status")
    assert res_st.status_code == 200
    assert "validated_samples_available" in res_st.json()

    # Start Training
    res_train = client.post(
        "/api/training/start",
        json={"epochs": 3, "batch_size": 16, "learning_rate": 0.001, "role": "ADMIN"}
    )
    assert res_train.status_code == 200
    assert res_train.json()["status"] in ["RUNNING", "COMPLETED"]

    time.sleep(1.2)

    # Create Federated Round
    res_round = client.post(
        "/api/federated/rounds",
        json={"base_model_version": "1.0.0", "participating_edges": ["EDGE-SECTOR-A-01", "EDGE-SECTOR-A-02"], "role": "ADMIN"}
    )
    assert res_round.status_code == 200
    round_id = res_round.json()["round_id"]

    # Aggregate Round
    res_agg = client.post(f"/api/federated/rounds/{round_id}/aggregate")
    assert res_agg.status_code == 200
    agg_data = res_agg.json()
    assert agg_data["status"] == "COMPLETED"
    assert agg_data["candidate_version"] == "1.1.0"


def test_candidate_validation_approval_deployment_and_rollback_api():
    """Tests candidate validation, approval, deployment, and rollback via API."""
    simulation_engine.reset_simulation()

    # 1. Create round and aggregate
    res_round = client.post("/api/federated/rounds", json={"base_model_version": "1.0.0"})
    round_id = res_round.json()["round_id"]
    res_agg = client.post(f"/api/federated/rounds/{round_id}/aggregate")
    cand_id = res_agg.json()["candidate_model_id"]

    # 2. Validate Candidate
    res_val = client.post(f"/api/models/{cand_id}/validate")
    assert res_val.status_code == 200
    assert "overall_mAP" in res_val.json()

    # 3. Approve Candidate
    res_app = client.post(
        f"/api/models/{cand_id}/approve",
        json={"operator_id": "SUP-001", "role": "SUPERVISOR", "notes": "Approved for deployment"}
    )
    assert res_app.status_code == 200
    assert res_app.json()["validation_status"] == "APPROVED"

    # 4. Deploy Candidate
    res_dep = client.post(
        f"/api/models/{cand_id}/deploy",
        json={"operator_id": "ADMIN-001", "role": "ADMIN", "notes": "Production push"}
    )
    assert res_dep.status_code == 200
    assert res_dep.json()["status"] == "ACTIVE"
    assert res_dep.json()["version"] == "1.1.0"

    # 5. Rollback
    res_roll = client.post(
        "/api/models/rollback",
        json={"operator_id": "ADMIN-001", "role": "ADMIN", "reason": "Test rollback"}
    )
    assert res_roll.status_code == 200
    assert res_roll.json()["status"] == "ROLLBACK_SUCCESSFUL"
    assert res_roll.json()["restored_version"] == "1.0.0"


def test_privacy_status_api():
    """Tests GET /api/federated/privacy."""
    res = client.get("/api/federated/privacy")
    assert res.status_code == 200
    data = res.json()
    assert data["raw_cctv_shared"] is False
    assert data["raw_images_shared"] is False
    assert data["model_updates_shared"] is True
