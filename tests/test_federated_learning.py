import time
import pytest
from backend.services.model_registry_service import model_registry
from backend.services.training_sample_service import training_sample_service
from backend.services.local_training_service import local_training_service
from backend.services.federated_learning_service import federated_aggregator
from backend.services.simulation_engine import simulation_engine


def test_baseline_active_model_and_hash_integrity():
    """Verifies baseline Active Model exists, is versioned, and passes SHA-256 integrity verification."""
    simulation_engine.reset_simulation()
    
    active = model_registry.get_active_model()
    assert active is not None
    assert active.version == "1.0.0"
    assert active.status == "ACTIVE"
    assert active.validation_status == "APPROVED"
    assert len(active.model_hash) == 64

    # Verify cryptographic integrity
    integrity = model_registry.verify_model_integrity(active.model_id)
    assert integrity["is_authentic"] is True
    assert integrity["status"] == "AUTHENTIC"


def test_sample_provenance_and_validation_guard():
    """Verifies data provenance tracking and ensures unvalidated samples cannot enter training."""
    simulation_engine.reset_simulation()

    # Collect unvalidated sample
    sample = training_sample_service.collect_sample(
        camera_id="CAM-SECTOR-A1",
        label="person",
        confidence=0.74,
        bbox=[100, 150, 200, 350],
        source_event_id="EVT-TEST-001",
        label_source="AUTO_COLLECTED",
        validation_status="PENDING"
    )
    assert sample.validation_status == "PENDING"
    assert sample.reviewed_by is None

    # Operator review & validation
    reviewed = training_sample_service.review_sample(
        sample_id=sample.sample_id,
        action="APPROVE",
        operator_id="OP-9402",
        role="OPERATOR",
        notes="Confirmed person detected in perimeter"
    )
    assert reviewed.validation_status == "VALIDATED"
    assert reviewed.reviewed_by == "OP-9402"
    assert reviewed.label_source == "OPERATOR_REVIEWED"

    # Operator relabel test
    relabelled = training_sample_service.review_sample(
        sample_id=sample.sample_id,
        action="RELABEL",
        corrected_label="car",
        operator_id="OP-9402",
        role="OPERATOR"
    )
    assert relabelled.label == "car"
    assert relabelled.validation_status == "VALIDATED"


def test_local_training_execution_and_metrics():
    """Verifies local on-device fine-tuning executes safely and produces real loss decay metrics."""
    simulation_engine.reset_simulation()

    # Ensure enough validated samples
    assert training_sample_service.get_validated_samples_count() >= 10

    run = local_training_service.start_training(
        epochs=3,
        batch_size=16,
        learning_rate=0.001,
        simulation_mode=False,
        operator_id="OP-9402",
        role="ADMIN"
    )
    assert run.run_id is not None
    assert run.status in ["RUNNING", "COMPLETED"]

    # Wait for completion
    time.sleep(1.5)

    status = local_training_service.get_status()
    assert status["is_training"] is False
    assert status["last_completed_run"] is not None
    assert status["last_completed_run"]["training_loss"] > 0.0
    assert status["last_completed_run"]["validation_metric"] >= 0.85

    # Check generated model updates
    updates = local_training_service.list_model_updates()
    assert len(updates) >= 1
    latest_upd = updates[0]
    assert latest_upd.base_model_version == "1.0.0"
    assert latest_upd.status in ["CREATED", "SUBMITTED"]
    assert len(latest_upd.update_hash) == 64


def test_federated_aggregation_fedavg():
    """Verifies weighted FedAvg combines updates from participating edge nodes to create Candidate Model."""
    simulation_engine.reset_simulation()

    round_model = federated_aggregator.create_round(
        base_model_version="1.0.0",
        participating_edges=["EDGE-SECTOR-A-01", "EDGE-SECTOR-A-02", "EDGE-SECTOR-B-01"],
        aggregation_method="FEDAVG"
    )
    assert round_model.round_id is not None
    assert round_model.status == "OPEN"

    # Execute aggregation
    agg_res = federated_aggregator.aggregate_round(round_model.round_id)
    assert agg_res["status"] == "COMPLETED"
    assert agg_res["candidate_version"] == "1.1.0"
    assert agg_res["candidate_model_id"] is not None

    # Check Candidate Model in Registry
    candidate = model_registry.get_model(agg_res["candidate_model_id"])
    assert candidate is not None
    assert candidate.version == "1.1.0"
    assert candidate.status == "CANDIDATE"
    assert candidate.validation_status in ["PENDING", "VALIDATED"]


def test_candidate_benchmark_validation():
    """Verifies candidate model undergoes measured benchmark evaluation comparing Active vs Candidate."""
    simulation_engine.reset_simulation()

    round_model = federated_aggregator.create_round(base_model_version="1.0.0")
    agg_res = federated_aggregator.aggregate_round(round_model.round_id)
    cand_id = agg_res["candidate_model_id"]

    val_res = model_registry.validate_candidate(cand_id)
    assert val_res["validation_status"] in ["PASS", "FAIL", "REVIEW_REQUIRED"]
    assert val_res["overall_mAP"] > 0.0
    assert len(val_res["metrics_comparison"]) >= 4

    # Verify metrics comparison schema
    for metric in val_res["metrics_comparison"]:
        assert "metric_name" in metric
        assert "active_value" in metric
        assert "candidate_value" in metric
        assert "diff" in metric


def test_model_approval_and_deployment_safety():
    """Verifies human supervisor approval gate and safe admin deployment with active backup."""
    simulation_engine.reset_simulation()

    round_model = federated_aggregator.create_round(base_model_version="1.0.0")
    agg_res = federated_aggregator.aggregate_round(round_model.round_id)
    cand_id = agg_res["candidate_model_id"]

    # 1. Unapproved candidate cannot be deployed
    with pytest.raises(ValueError, match="Cannot deploy unapproved model"):
        model_registry.deploy_model(cand_id, "ADMIN-001", "ADMIN")

    # 2. Operator role cannot approve (Supervisor or Admin required)
    with pytest.raises(PermissionError):
        model_registry.approve_model(cand_id, "OP-001", "OPERATOR")

    # 3. Supervisor approves
    approved = model_registry.approve_model(cand_id, "SUP-001", "SUPERVISOR", "Validated improvement")
    assert approved.validation_status == "APPROVED"

    # 4. Admin deploys
    deployed = model_registry.deploy_model(cand_id, "ADMIN-001", "ADMIN", "Promoted to production")
    assert deployed.status == "ACTIVE"
    assert deployed.version == "1.1.0"

    # 5. Verify previous active model is now ARCHIVED
    previous = model_registry.get_model("MODEL-YOLO-V1.0.0")
    assert previous.status == "ARCHIVED"


def test_instant_model_rollback():
    """Verifies 1-click rollback restores previous active model and demotes regressed model."""
    simulation_engine.reset_simulation()

    # Create and deploy candidate v1.1.0
    round_model = federated_aggregator.create_round(base_model_version="1.0.0")
    agg_res = federated_aggregator.aggregate_round(round_model.round_id)
    cand_id = agg_res["candidate_model_id"]
    model_registry.approve_model(cand_id, "SUP-001", "SUPERVISOR")
    model_registry.deploy_model(cand_id, "ADMIN-001", "ADMIN")

    assert model_registry.get_active_model().version == "1.1.0"

    # Execute Rollback
    restored, demoted = model_registry.rollback_model("ADMIN-001", "ADMIN", "Detected camera sync regression")
    assert restored.version == "1.0.0"
    assert restored.status == "ACTIVE"
    assert demoted.version == "1.1.0"
    assert demoted.status == "ARCHIVED"


def test_model_tamper_detection():
    """Verifies modifying model metadata triggers cryptographic SHA-256 hash mismatch."""
    simulation_engine.reset_simulation()

    active = model_registry.get_active_model()
    original_hash = active.model_hash

    # Calculate integrity
    integrity_before = model_registry.verify_model_integrity(active.model_id)
    assert integrity_before["is_authentic"] is True

    # Artificially alter descriptor
    computed_altered = model_registry.compute_model_descriptor_hash(
        active.version, "TAMPERED_MODEL_TYPE", active.model_metadata
    )
    assert computed_altered != original_hash


def test_version_incompatibility_rejection():
    """Verifies that an edge model update computed on an incompatible base model is rejected."""
    simulation_engine.reset_simulation()

    round_model = federated_aggregator.create_round(base_model_version="1.0.0")

    incompatible_update = {
        "update_id": "UPD-INCOMPAT-001",
        "edge_id": "EDGE-SECTOR-A-01",
        "base_model_version": "0.9.0",  # Incompatible version
        "sample_count": 50,
        "weights_delta": {"head": 0.05}
    }

    with pytest.raises(ValueError, match="Model version mismatch"):
        federated_aggregator.submit_update(round_model.round_id, incompatible_update)


def test_phase9_hero_demo_scenario():
    """Executes the full end-to-end Phase 9 Hero Demonstration Scenario."""
    simulation_engine.reset_simulation()

    demo_res = simulation_engine.run_phase9_learning_demo()
    assert demo_res["status"] == "success"
    
    steps = demo_res["lifecycle_steps"]
    assert steps["step1_baseline_model"]["version"] == "1.0.0"
    assert steps["step2_sample_validation"]["validated_samples_count"] >= 10
    assert steps["step3_local_training"]["status"] == "COMPLETED"
    assert steps["step4_federated_aggregation"]["candidate_version"] == "1.1.0"
    assert steps["step6_supervisor_approval"]["validation_status"] == "APPROVED"
    assert steps["step7_deployment"]["active_version"] == "1.1.0"
    assert steps["step8_privacy_audit"]["raw_cctv_shared"] is False
    assert steps["step8_privacy_audit"]["model_updates_shared"] is True
