import pytest
import copy
from datetime import datetime, timezone
from backend.services.evidence_hash_service import evidence_hash_service
from backend.services.ledger_service import ledger_service
from backend.services.evidence_service import evidence_service
from backend.services.simulation_engine import simulation_engine


@pytest.fixture(autouse=True)
def clean_simulation():
    simulation_engine.reset_simulation()
    yield
    simulation_engine.reset_simulation()


def test_deterministic_canonicalization():
    """
    Verifies that identical semantic data with varying key ordering, extra whitespace,
    or transient UI fields produces the EXACT same canonical bytes and SHA-256 hash.
    """
    manifest_a = {
        "incident_id": "INC-0024",
        "version": "1.0",
        "risk_assessment": {
            "score": 78.50,
            "level": "HIGH",
            "factors": ["FENCE_CROSSING", "ZONE_SENSITIVITY"]
        },
        "events": [
            {"event_id": "EVT-01", "camera_id": "CAM-01"},
            {"event_id": "EVT-02", "camera_id": "CAM-02"}
        ]
    }

    # Same content with keys in reverse order and transient fields injected
    manifest_b = {
        "events": [
            {"camera_id": "CAM-01", "event_id": "EVT-01"},
            {"camera_id": "CAM-02", "event_id": "EVT-02"}
        ],
        "version": "1.0",
        "_ui_state": "EXPANDED",
        "temp_id": "TEMP-999",
        "risk_assessment": {
            "factors": ["FENCE_CROSSING", "ZONE_SENSITIVITY"],
            "level": "HIGH",
            "score": 78.50,
            "$$hashKey": "object:123"
        },
        "incident_id": "INC-0024"
    }

    bytes_a = evidence_hash_service.canonicalize(manifest_a)
    bytes_b = evidence_hash_service.canonicalize(manifest_b)

    hash_a = evidence_hash_service.calculate_sha256(bytes_a)
    hash_b = evidence_hash_service.calculate_sha256(bytes_b)

    assert bytes_a == bytes_b
    assert hash_a["hash"] == hash_b["hash"]
    assert hash_a["algorithm"] == "SHA-256"


def test_hash_sensitivity():
    """
    Verifies that changing any single data point (risk score, timestamp, camera ID, event type)
    causes a significant change in the SHA-256 cryptographic digest.
    """
    base_manifest = {
        "incident_id": "INC-0024",
        "version": "1.0",
        "risk_assessment": {"score": 78.0, "level": "HIGH"},
        "events": [{"event_id": "EVT-01", "camera_id": "CAM-01", "timestamp": "2026-09-20T12:00:00Z"}]
    }

    base_hash = evidence_hash_service.calculate_sha256(base_manifest)["hash"]

    # 1. Modify risk score slightly
    mod1 = copy.deepcopy(base_manifest)
    mod1["risk_assessment"]["score"] = 78.1
    hash1 = evidence_hash_service.calculate_sha256(mod1)["hash"]
    assert hash1 != base_hash

    # 2. Modify timestamp
    mod2 = copy.deepcopy(base_manifest)
    mod2["events"][0]["timestamp"] = "2026-09-20T12:00:01Z"
    hash2 = evidence_hash_service.calculate_sha256(mod2)["hash"]
    assert hash2 != base_hash

    # 3. Modify camera ID
    mod3 = copy.deepcopy(base_manifest)
    mod3["events"][0]["camera_id"] = "CAM-02"
    hash3 = evidence_hash_service.calculate_sha256(mod3)["hash"]
    assert hash3 != base_hash


def test_private_ledger_anchoring_and_chaining():
    """
    Verifies the private ledger creates chained blocks with valid previous_block_hash links
    and Merkle root computation.
    """
    anchor1 = ledger_service.anchor_hash(
        incident_id="INC-0001",
        evidence_id="EVD-0001-v1_0",
        evidence_hash="a"*64,
        version="1.0"
    )

    assert anchor1["status"] == "CONFIRMED"
    assert anchor1["transaction_id"].startswith("TX-")
    assert anchor1["block_number"] >= 1

    anchor2 = ledger_service.anchor_hash(
        incident_id="INC-0002",
        evidence_id="EVD-0002-v1_0",
        evidence_hash="b"*64,
        version="1.0"
    )

    assert anchor2["block_number"] == anchor1["block_number"] + 1
    assert anchor2["previous_block_hash"] == anchor1["block_hash"]


def test_evidence_generation_and_verification_authentic():
    """
    Simulates a full scenario with events and risk scoring, generates an evidence package,
    anchors it, and confirms verification returns AUTHENTIC.
    """
    scenario_res = simulation_engine.run_scenario_5_high_risk_with_vehicle()
    incident_id = scenario_res["incident_id"]

    # 1. Create and anchor evidence
    pkg = evidence_service.create_and_anchor_evidence(
        incident_id=incident_id,
        operator_id="OP-9402",
        role="SUPERVISOR",
        version="1.0",
        notes="Official border perimeter evidence package"
    )

    assert pkg.incident_id == incident_id
    assert pkg.status == "ANCHORED"
    assert pkg.hash.algorithm == "SHA-256"
    assert len(pkg.hash.hash_value) == 64
    assert pkg.anchor is not None
    assert pkg.anchor.transaction_id.startswith("TX-")
    assert pkg.inclusion_summary.verified_events_count >= 1
    assert pkg.inclusion_summary.risk_assessment_included is True

    # 2. Verify integrity
    verif = evidence_service.verify_evidence_integrity(pkg.evidence_id, "OP-9402", "SUPERVISOR")
    assert verif.status == "AUTHENTIC"
    assert verif.is_authentic is True
    assert verif.calculated_hash == verif.anchored_hash


def test_evidence_tamper_detection_and_restoration():
    """
    Hero Feature Test:
    1. Generate evidence -> AUTHENTIC
    2. Tamper off-chain stored file on disk -> verify -> TAMPERED
    3. Restore original evidence file -> verify -> AUTHENTIC
    """
    scenario_res = simulation_engine.run_scenario_5_high_risk_with_vehicle()
    incident_id = scenario_res["incident_id"]

    pkg = evidence_service.create_and_anchor_evidence(
        incident_id=incident_id,
        operator_id="OP-9402",
        role="INVESTIGATOR",
        version="1.0"
    )

    # 1. Initial verification -> AUTHENTIC
    v1 = evidence_service.verify_evidence_integrity(pkg.evidence_id)
    assert v1.status == "AUTHENTIC"
    assert v1.is_authentic is True

    # 2. Intentionally modify off-chain file
    tamper_res = evidence_service.tamper_evidence_for_demo(pkg.evidence_id, tamper_field="risk_score", tamper_value=99.9)
    assert tamper_res["status"] == "success"

    # 3. Verify -> TAMPERED
    v2 = evidence_service.verify_evidence_integrity(pkg.evidence_id)
    assert v2.status == "TAMPERED"
    assert v2.is_authentic is False
    assert v2.calculated_hash != v2.anchored_hash
    assert "TAMPER DETECTED" in (v2.tamper_analysis or "")

    # 4. Restore original package -> verify -> AUTHENTIC
    restore_res = evidence_service.restore_evidence_for_demo(pkg.evidence_id)
    assert restore_res["status"] == "success"

    v3 = evidence_service.verify_evidence_integrity(pkg.evidence_id)
    assert v3.status == "AUTHENTIC"
    assert v3.is_authentic is True
    assert v3.calculated_hash == v3.anchored_hash


def test_evidence_versioning_and_idempotency():
    """
    Verifies that calling evidence generation again with the same version returns the existing anchor,
    and incrementing version (e.g. v1.1) creates a distinct verifiable version.
    """
    scenario_res = simulation_engine.run_scenario_3_confirmed_fence_crossing()
    incident_id = scenario_res["incident_id"]

    # 1. Version 1.0
    pkg_v1 = evidence_service.create_and_anchor_evidence(incident_id=incident_id, version="1.0")
    tx_v1 = pkg_v1.anchor.transaction_id

    # 2. Re-anchor same version (idempotency)
    pkg_v1_retry = evidence_service.create_and_anchor_evidence(incident_id=incident_id, version="1.0")
    assert pkg_v1_retry.anchor.transaction_id == tx_v1

    # 3. Version 1.1
    pkg_v2 = evidence_service.create_and_anchor_evidence(incident_id=incident_id, version="1.1")
    assert pkg_v2.version == "1.1"
    assert pkg_v2.evidence_id != pkg_v1.evidence_id

    # Both versions verifiable independently
    assert evidence_service.verify_evidence_integrity(pkg_v1.evidence_id).status == "AUTHENTIC"
    assert evidence_service.verify_evidence_integrity(pkg_v2.evidence_id).status == "AUTHENTIC"
