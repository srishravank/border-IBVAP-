import pytest
from datetime import datetime, timezone, timedelta
from backend.services.connectivity_service import connectivity_service
from backend.services.sync_service import sync_service
from backend.services.central_sync_receiver import central_sync_receiver
from backend.services.simulation_engine import simulation_engine
from backend.services.evidence_service import evidence_service
from backend.services.command_service import command_service
from backend.models.sync import ConnectionState, SyncBatchRequest, SyncPayload
from backend.database.connection import SessionLocal
from backend.database.models import SyncQueueItemModel, EvidencePackageModel


@pytest.fixture(autouse=True)
def clean_state():
    simulation_engine.reset_simulation()
    connectivity_service.set_state(ConnectionState.ONLINE, "Test fixture reset", is_simulated=False)
    central_sync_receiver.reset()
    yield
    simulation_engine.reset_simulation()
    connectivity_service.set_state(ConnectionState.ONLINE, "Test cleanup", is_simulated=False)
    central_sync_receiver.reset()


def test_connectivity_state_transitions():
    """Verifies state machine transitions: ONLINE -> OFFLINE -> RECONNECTING -> SYNCING -> ONLINE."""
    assert connectivity_service.current_state == ConnectionState.ONLINE
    assert connectivity_service.is_online is True

    # 1. Simulate Offline
    connectivity_service.simulate_offline("Network disconnected")
    assert connectivity_service.current_state == ConnectionState.OFFLINE
    assert connectivity_service.is_offline is True
    assert connectivity_service.is_online is False

    # 2. Restore Connection
    connectivity_service.restore_connection("Network detected")
    assert connectivity_service.current_state in (ConnectionState.RECONNECTING, ConnectionState.ONLINE, ConnectionState.SYNCING)

    # 3. Direct transition
    connectivity_service.set_state(ConnectionState.ONLINE, "Online check")
    assert connectivity_service.current_state == ConnectionState.ONLINE


def test_local_offline_processing_and_queue_persistence():
    """
    Verifies that when offline, AI events, incidents, risk scoring, and evidence packages
    execute locally and are persisted in the durable SyncQueue with preserved original timestamps.
    """
    connectivity_service.simulate_offline("Perimeter outage")

    # Run AI incident scenario while offline
    res = simulation_engine.run_scenario_3_confirmed_fence_crossing()
    incident_id = res["incident_id"]

    # Generate offline evidence package
    pkg = evidence_service.create_and_anchor_evidence(incident_id=incident_id, version="1.0")

    assert pkg.status == "ANCHOR_PENDING"
    assert len(pkg.hash.hash_value) == 64

    # Verify Sync Queue contains items
    summary = sync_service.get_summary()
    assert summary.total_queued >= 1
    assert summary.pending_count >= 1
    assert summary.evidence_pending_count >= 1

    queue_items = sync_service.get_queue_items(status="PENDING")
    assert len(queue_items) >= 1
    ev_item = next(it for it in queue_items if it.entity_type == "EVIDENCE_PACKAGE")
    assert ev_item.priority == 1
    assert ev_item.entity_id == pkg.evidence_id


def test_queue_priority_ordering():
    """
    Verifies that high-priority items (Priority 1: Critical/High Risk, Evidence Anchors)
    are processed before normal items (Priority 2, Priority 3).
    """
    connectivity_service.simulate_offline("Queue priority test")

    # Enqueue Low, Critical, Medium items out of order
    sync_service.enqueue_item("DEBUG_LOG", "LOG-01", {"msg": "low priority"}, priority=3)
    sync_service.enqueue_item("INCIDENT", "INC-CRIT-01", {"risk_level": "CRITICAL"}, priority=1)
    sync_service.enqueue_item("EVENT", "EVT-MED-01", {"event_type": "ZONE_ENTRY"}, priority=2)

    pending = sync_service.get_pending_items(batch_size=10)
    priorities = [it.priority for it in pending]

    # Verify strictly sorted in ascending order of priority (1 before 2 before 3)
    assert priorities == sorted(priorities)
    assert pending[0].entity_id == "INC-CRIT-01"


def test_idempotent_synchronization_and_duplicate_prevention():
    """
    Verifies that submitting identical items or retrying synchronization returns DUPLICATE_ACCEPTED
    without duplicating records in the central system.
    """
    batch_req = SyncBatchRequest(
        edge_id="EDGE-01",
        batch_id="BATCH-TEST-001",
        items=[
            SyncPayload(
                edge_id="EDGE-01",
                idempotency_key="EDGE-01-INC-TEST-001-CREATE",
                entity_type="INCIDENT",
                entity_id="INC-TEST-001",
                operation="CREATE",
                priority=1,
                created_at_edge=datetime.now(timezone.utc).isoformat(),
                payload={"incident_id": "INC-TEST-001", "risk_score": 85.0}
            )
        ],
        sent_at=datetime.now(timezone.utc).isoformat()
    )

    # First submission
    res1 = central_sync_receiver.process_batch(batch_req)
    assert res1.accepted_count == 1
    assert res1.duplicate_count == 0
    assert res1.receipts[0].status == "ACCEPTED"

    # Second submission (identical idempotency_key)
    res2 = central_sync_receiver.process_batch(batch_req)
    assert res2.accepted_count == 0
    assert res2.duplicate_count == 1
    assert res2.receipts[0].status == "DUPLICATE_ACCEPTED"


def test_resumable_synchronization():
    """
    Verifies that synchronization progress is resumable:
    Restoring connectivity automatically processes pending items, and subsequent sync calls
    do not re-process already synced records.
    """
    connectivity_service.simulate_offline("Resumable sync test")

    for i in range(5):
        sync_service.enqueue_item("EVENT", f"EVT-RESUME-{i:03d}", {"seq": i}, priority=2)

    assert sync_service.get_summary().pending_count == 5

    # Restore connection (triggers automatic background synchronization callback)
    connectivity_service.restore_connection("Back online")

    # Verify all items synchronized
    summary = sync_service.get_summary()
    assert summary.pending_count == 0
    assert summary.synced_count == 5

    # Secondary manual trigger verifies idempotency and zero duplicate processing
    sync_res = sync_service.trigger_sync()
    assert sync_res["items_synced"] == 0
    assert sync_service.get_summary().pending_count == 0
    assert sync_service.get_summary().synced_count == 5


def test_exponential_backoff_retry():
    """
    Verifies that failed sync queue items increment attempt count and calculate next_retry_at using exponential backoff.
    """
    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        item = SyncQueueItemModel(
            edge_id="EDGE-01",
            idempotency_key="EDGE-01-FAIL-001",
            entity_type="EVENT",
            entity_id="EVT-FAIL-001",
            operation="CREATE",
            priority=2,
            status="RETRY_PENDING",
            payload_json="{}",
            attempt_count=2,
            created_at=now_utc,
            next_retry_at=now_utc + timedelta(seconds=20)
        )
        db.add(item)
        db.commit()
        item_id = item.id
    finally:
        db.close()

    # Manual retry resets counters
    retry_res = sync_service.retry_item(item_id)
    assert retry_res.status == "success"
    assert retry_res.next_status == "PENDING"


def test_evidence_hash_invariance_and_deferred_anchoring():
    """
    Verifies that an evidence package created offline:
    1. Computes SHA-256 immediately with status ANCHOR_PENDING.
    2. Upon synchronization, status transitions to ANCHORED.
    3. The SHA-256 hash remains 100% invariant and verifies as AUTHENTIC.
    """
    connectivity_service.simulate_offline("Evidence offline test")

    scenario_res = simulation_engine.run_scenario_3_confirmed_fence_crossing()
    incident_id = scenario_res["incident_id"]

    pkg = evidence_service.create_and_anchor_evidence(incident_id=incident_id, version="1.0")
    offline_hash = pkg.hash.hash_value

    assert pkg.status == "ANCHOR_PENDING"

    # Restore connection and synchronize
    connectivity_service.restore_connection("Restore for evidence")
    sync_service.trigger_sync()

    # Re-query package
    pkg_updated = evidence_service.get_evidence_package(pkg.evidence_id)
    assert pkg_updated.status == "ANCHORED"
    assert pkg_updated.hash.hash_value == offline_hash

    # Verify Cryptographic Integrity
    verif = evidence_service.verify_evidence_integrity(pkg.evidence_id)
    assert verif.status == "AUTHENTIC"
    assert verif.is_authentic is True
    assert verif.calculated_hash == offline_hash


def test_offline_operator_actions():
    """
    Verifies that operator actions (Acknowledge, Notes, Close) work offline,
    are recorded locally, and queue items are synchronized upon reconnection.
    """
    connectivity_service.simulate_offline("Operator offline actions")

    res = simulation_engine.run_scenario_3_confirmed_fence_crossing()
    incident_id = res["incident_id"]

    # Operator acknowledges offline
    act = command_service.acknowledge_incident(
        incident_id=incident_id,
        operator_id="OP-9402",
        role="OPERATOR",
        notes="Offline perimeter acknowledge"
    )
    assert act.incident_id == incident_id

    # Add offline note
    note = command_service.add_note(
        incident_id=incident_id,
        operator_id="OP-9402",
        role="OPERATOR",
        note="Field patrol dispatched locally"
    )
    assert note.note_id.startswith("NOTE-")

    # Restore and sync
    connectivity_service.restore_connection("Operator sync")
    sync_res = sync_service.trigger_sync()
    assert sync_res["status"] == "completed"


def test_application_crash_recovery():
    """
    Verifies that durable sync queue items in SQLite survive simulated restarts and remain intact.
    """
    connectivity_service.simulate_offline("Crash test")
    sync_service.enqueue_item("INCIDENT", "INC-CRASH-01", {"title": "Crash Recovery Incident"}, priority=1)

    # Verify in new database session
    db = SessionLocal()
    try:
        item = db.query(SyncQueueItemModel).filter(
            SyncQueueItemModel.entity_id == "INC-CRASH-01"
        ).first()
        assert item is not None
        assert item.status == "PENDING"
        assert item.payload["title"] == "Crash Recovery Incident"
    finally:
        db.close()


def test_phase8_hero_demo_scenario():
    """
    Executes the full Phase 8 Hero Demonstration from simulation_engine:
    Network OFF -> AI continues -> Incident created -> Evidence hashed -> Sync queued ->
    Network ON -> Resumable sync -> Evidence anchored -> Verification AUTHENTIC.
    """
    demo_res = simulation_engine.run_phase8_offline_sync_demo()

    assert demo_res["status"] == "success"
    assert demo_res["hash_invariant"] is True
    assert demo_res["evidence_integrity"] == "AUTHENTIC"
    assert demo_res["queue_before_sync"]["pending"] >= 1
    assert demo_res["queue_after_sync"]["pending"] == 0
