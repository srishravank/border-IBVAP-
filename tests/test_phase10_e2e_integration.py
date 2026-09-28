import time
import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.detection import DetectionResult
from backend.services.camera_manager import camera_manager
from backend.services.ai_pipeline import ai_service
from backend.services.event_manager import event_manager
from backend.services.cross_camera_engine import cross_camera_engine
from backend.services.risk_service import risk_service
from backend.services.command_service import command_service
from backend.services.evidence_service import evidence_service
from backend.services.connectivity_service import connectivity_service
from backend.services.sync_service import sync_service
from backend.services.model_registry_service import model_registry
from backend.services.training_sample_service import training_sample_service
from backend.services.local_training_service import local_training_service
from backend.services.federated_learning_service import federated_aggregator
from backend.services.simulation_engine import simulation_engine
from backend.models.security_event import SecurityEventResponse, SecurityEventType, EventStatus, VerificationDetail
from ai.schemas.observation import AIObservation, ObservedObjectSummary
from verification.temporal_gate import CandidateVerificationTracker


@pytest.fixture(autouse=True)
def clean_simulation():
    """Resets simulation before and after each test to maintain strict isolation."""
    simulation_engine.reset_simulation()
    connectivity_service.restore_connection("Test Setup")
    yield
    simulation_engine.reset_simulation()
    connectivity_service.restore_connection("Test Teardown")


def test_camera_to_detection():
    """Verify Phase 1 -> Phase 2: Frame ingestion to YOLO/RT-DETR detection."""
    from ai.detection.mock_detector import MockDetector
    detector = MockDetector()
    detector.load_model()
    dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    detections = detector.detect(dummy_frame)
    
    assert len(detections) >= 1
    assert detections[0].class_name in ["person", "vehicle", "car"]
    assert 0.0 <= detections[0].confidence <= 1.0
    assert len(detections[0].bbox) == 4


def test_detection_to_tracking():
    """Verify Phase 2: Detections to ByteTrack tracker track assignment."""
    from ai.tracking.bytetrack_tracker import ByteTrackTracker
    tracker = ByteTrackTracker(camera_id="CAM-01", track_thresh=0.4, match_thresh=0.8)
    
    dets = [
        DetectionResult(
            class_name="person",
            object_type="person",
            confidence=0.90,
            bbox=[100.0, 100.0, 200.0, 300.0],
            center=[150.0, 200.0]
        )
    ]
    tracks = tracker.update(dets)
    assert len(tracks) >= 1
    track = tracks[0]
    assert hasattr(track, "track_id")
    assert track.track_id > 0


def test_tracking_to_verification():
    """Verify Phase 2 -> Phase 3: Tracked observation through temporal verification gate."""
    tracker = CandidateVerificationTracker(
        candidate_key="CAM-01:17:ZONE-01:ZONE_INTRUSION",
        camera_id="CAM-01",
        track_id=17,
        zone_id="ZONE-01",
        event_type="ZONE_INTRUSION",
        required_frames=3,
        window_frames=5
    )
    
    obs = AIObservation(
        observation_id="OBS-TEST-100",
        camera_id="CAM-01",
        frame_id=100,
        object=ObservedObjectSummary(
            track_id=17,
            formatted_id="P017",
            type="person",
            class_name="person",
            confidence=0.92,
            bbox=[120.0, 100.0, 200.0, 300.0],
            center=[160.0, 200.0]
        ),
        trajectory=[[160.0, 190.0], [160.0, 200.0]]
    )
    
    s1, v1 = tracker.add_observation(obs)
    assert s1 == EventStatus.CANDIDATE
    
    obs.frame_id = 101
    s2, v2 = tracker.add_observation(obs)
    assert s2 == EventStatus.VERIFYING
    
    obs.frame_id = 102
    s3, v3 = tracker.add_observation(obs)
    assert s3 == EventStatus.CONFIRMED
    assert v3.verification_status == "PASSED"


def test_verification_to_correlation():
    """Verify Phase 3 -> Phase 4: Verified security event correlation into cross-camera engine."""
    cross_camera_engine.initialize()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    evt = SecurityEventResponse(
        event_id="EVT-TEST-CORR-01",
        camera_id="CAM-01",
        track_id=105,
        formatted_track_id="P105",
        zone_id="ZONE-CAM01-01",
        zone_name="Sector A Corridor",
        event_type=SecurityEventType.ZONE_ENTRY,
        status=EventStatus.CONFIRMED,
        created_at=now_iso,
        confidence=0.94,
        object_type="person",
        class_name="person",
        bbox=[400.0, 200.0, 460.0, 420.0],
        reference_point=[430.0, 420.0],
        verification=VerificationDetail(
            required_frames=3,
            confirmed_frames=3,
            verification_status="PASSED",
            supporting_frame_ids=[1, 2, 3],
            average_confidence=0.94
        ),
        description="Test verified entry"
    )
    
    cross_camera_engine.process_confirmed_event(evt)
    subj_id = cross_camera_engine.track_to_subject.get(("CAM-01", 105))
    assert subj_id is not None
    assert subj_id.startswith("SUBJ-")


def test_correlation_to_incident():
    """Verify Phase 4: Correlated subject creates unified Incident with incident graph."""
    res = simulation_engine.run_multi_camera_journey_demo()
    assert res["status"] == "success"
    incident_id = res["incident_id"]
    
    graph_data = cross_camera_engine.get_incident_graph(incident_id)
    assert graph_data is not None
    assert len(graph_data.nodes) >= 3
    assert len(graph_data.edges) >= 2


def test_incident_to_risk():
    """Verify Phase 4 -> Phase 5: Incident evaluated by explainable risk aggregator."""
    res = simulation_engine.run_multi_camera_journey_demo()
    incident_id = res["incident_id"]
    
    risk_assessment = risk_service.evaluate_incident(incident_id, force=True)
    assert risk_assessment is not None
    assert risk_assessment.score > 0.0
    assert risk_assessment.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert len(risk_assessment.factors) > 0
    assert len(risk_assessment.explanation) > 10


def test_risk_to_dashboard():
    """Verify Phase 5 -> Phase 6: Risk telemetry and alerts consumed by Command Center."""
    client = TestClient(app)
    simulation_engine.run_scenario_3_night_intrusion()
    
    response = client.get("/api/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert isinstance(alerts, list)
    assert len(alerts) >= 1


def test_operator_action():
    """Verify Phase 6: Human-in-the-loop operator action lifecycle (Ack, Note, Investigate, Close)."""
    res = simulation_engine.run_scenario_2_verified_zone_entry()
    incident_id = res["incident_id"]
    
    ack_res = command_service.acknowledge_incident(
        incident_id=incident_id,
        operator_id="OP-9402",
        role="OPERATOR",
        notes="Operator acknowledged intrusion."
    )
    assert ack_res.action == "ACKNOWLEDGED"
    
    note_res = command_service.add_note(
        incident_id=incident_id,
        operator_id="OP-9402",
        role="SUPERVISOR",
        note="Border patrol deployed to Sector B."
    )
    assert note_res.incident_id == incident_id


def test_evidence_generation_and_hash():
    """Verify Phase 7: Tamper-evident evidence package generation and SHA-256 hash calculation."""
    res = simulation_engine.run_multi_camera_journey_demo()
    incident_id = res["incident_id"]
    
    evidence_pkg = evidence_service.create_and_anchor_evidence(
        incident_id=incident_id,
        operator_id="OP-9402",
        role="SUPERVISOR",
        version="1.0",
        notes="Official evidence package"
    )
    assert evidence_pkg.evidence_id.startswith("EVD-")
    assert len(evidence_pkg.hash.hash_value) == 64
    
    verif = evidence_service.verify_evidence_integrity(evidence_pkg.evidence_id)
    assert verif.status == "AUTHENTIC"


def test_tamper_detection():
    """Verify Phase 7: Cryptographic tamper detection detects unauthorized manifest modifications."""
    res = simulation_engine.run_multi_camera_journey_demo()
    incident_id = res["incident_id"]
    
    pkg = evidence_service.create_and_anchor_evidence(
        incident_id=incident_id,
        operator_id="OP-9402",
        role="SUPERVISOR"
    )
    
    # Tamper with evidence
    evidence_service.demonstrate_tamper(pkg.evidence_id)
    tampered_verif = evidence_service.verify_evidence_integrity(pkg.evidence_id)
    assert tampered_verif.status == "TAMPERED"
    
    # Restore evidence
    evidence_service.restore_evidence(pkg.evidence_id)
    restored_verif = evidence_service.verify_evidence_integrity(pkg.evidence_id)
    assert restored_verif.status == "AUTHENTIC"


def test_offline_processing_and_sync_recovery():
    """Verify Phase 8: Offline queueing during disconnect and idempotent synchronization on reconnect."""
    demo_res = simulation_engine.run_phase8_offline_sync_demo()

    assert demo_res["status"] == "success"
    assert demo_res["hash_invariant"] is True
    assert demo_res["evidence_integrity"] == "AUTHENTIC"
    assert demo_res["queue_before_sync"]["pending"] >= 1
    assert demo_res["queue_after_sync"]["pending"] == 0


def test_duplicate_prevention():
    """Verify Phase 8: Synchronization idempotency prevents duplicate item injection."""
    queue_item = sync_service.enqueue_item("INCIDENT_ACK", "INC-TEST-DUP-01", {"status": "ACK"})
    
    # Synchronize twice
    sync_service.trigger_sync()
    second_sync = sync_service.trigger_sync()
    
    assert second_sync["items_synced"] == 0
    assert second_sync["items_failed"] == 0


def test_training_sample_validation_and_triage():
    """Verify Phase 9: Human-in-the-loop sample review triage (APPROVE, REJECT, RELABEL)."""
    training_sample_service.seed_demo_samples(count=5)
    samples = training_sample_service.get_samples(limit=10)
    assert len(samples) >= 5
    
    first_id = samples[0].sample_id
    appr = training_sample_service.review_sample(first_id, "APPROVE", "OP-9402", "OPERATOR")
    assert appr.validation_status == "VALIDATED"


def test_model_lifecycle_full_flow():
    """Verify Phase 9: Candidate validation -> Supervisor approval -> Safe deploy -> Rollback."""
    # 1. Local Training
    run = local_training_service.start_training(epochs=2, simulation_mode=True)
    assert run.run_id is not None
    time.sleep(1.2)
    
    # 2. Federated Round & Aggregation
    f_round = federated_aggregator.create_round()
    updates = local_training_service.list_model_updates()
    assert len(updates) >= 1
    update = updates[0]
    federated_aggregator.submit_update(f_round.round_id, update)
    agg_res = federated_aggregator.aggregate_round(f_round.round_id)
    candidate_id = agg_res["candidate_model_id"]
    
    # 3. Benchmark Validation Gate
    val_res = model_registry.validate_candidate(candidate_id)
    assert val_res["validation_status"] == "PASS"
    
    # 4. Supervisor Approval
    appr_m = model_registry.approve_model(candidate_id, "OP-9402", "SUPERVISOR")
    assert appr_m.validation_status == "APPROVED"
    
    # 5. Safe Deployment
    dep_m = model_registry.deploy_model(candidate_id, "OP-9402", "ADMIN")
    assert dep_m.status == "ACTIVE"
    
    # 6. Instant Rollback
    restored, demoted = model_registry.rollback_model("OP-9402", "ADMIN", "Testing Rollback")
    assert restored.version == "1.0.0"
    assert demoted.status == "ARCHIVED"


def test_master_e2e_pipeline_full_run():
    """Verify Phase 10: Master End-to-End Demonstration scenario (Parts A through J)."""
    master_result = simulation_engine.run_master_e2e_demo()
    
    assert master_result["status"] == "SUCCESS"
    assert master_result["final_status"] == "READY_FOR_JURY_DEMONSTRATION"
    
    summary = master_result["pipeline_summary"]
    assert summary["see"]["status"] == "PASSED"
    assert summary["understand_verify_correlate"]["status"] == "PASSED"
    assert summary["assess"]["status"] == "PASSED"
    assert summary["respond"]["status"] == "PASSED"
    assert summary["prove"]["status"] == "PASSED"
    assert summary["prove"]["verification_authentic"] is True
    assert summary["prove"]["tamper_detection"] is True
    assert summary["offline_recover"]["status"] == "PASSED"
    assert summary["learn"]["status"] == "PASSED"


def test_unified_health_check_endpoint():
    """Verify Phase 10: Unified /api/system/health endpoint checks all subsystems."""
    client = TestClient(app)
    resp = client.get("/api/system/health")
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "services" in data
    
    services = data["services"]
    assert "database" in services
    assert "camera_pipeline" in services
    assert "ai_engine" in services
    assert "risk_engine" in services
    assert "evidence" in services
    assert "ledger" in services
    assert "sync" in services
    assert "learning" in services
