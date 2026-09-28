import pytest
from datetime import datetime, timezone

from backend.database.connection import init_db
from backend.services.simulation_engine import simulation_engine
from backend.services.cross_camera_engine import cross_camera_engine
from backend.services.command_service import command_service


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    simulation_engine.reset_simulation()
    yield
    simulation_engine.reset_simulation()


def test_incident_lifecycle_transitions():
    """Tests the standard operator lifecycle: DETECTED -> VERIFIED -> CORRELATED -> ASSESSED -> ACKNOWLEDGED -> INVESTIGATING -> CLOSED."""
    # Generate an incident via scenario
    res = simulation_engine.run_scenario_3_confirmed_fence_crossing()
    incident_id = res["incident_id"]

    # Initial lifecycle check
    lifecycle = command_service.get_incident_lifecycle(incident_id)
    assert lifecycle is not None
    assert lifecycle.current_status in ("ASSESSED", "ACTIVE")
    assert len(lifecycle.stages) == 7

    # Stage 1: Acknowledge incident
    ok, msg, lc1 = command_service.transition_incident_status(
        incident_id=incident_id,
        target_status="ACKNOWLEDGED",
        operator_id="OP-001",
        role="OPERATOR",
        notes="Operator acknowledged intrusion alarm"
    )
    assert ok is True
    assert lc1.current_status == "ACKNOWLEDGED"
    ack_stage = next(s for s in lc1.stages if s.stage == "ACKNOWLEDGED")
    assert ack_stage.is_completed is True
    assert ack_stage.operator_id == "OP-001"

    # Stage 2: Start Investigation
    ok, msg, lc2 = command_service.transition_incident_status(
        incident_id=incident_id,
        target_status="INVESTIGATING",
        operator_id="OP-002",
        role="INVESTIGATOR",
        notes="Investigator examining camera feeds and timeline"
    )
    assert ok is True
    assert lc2.current_status == "INVESTIGATING"
    inv_stage = next(s for s in lc2.stages if s.stage == "INVESTIGATING")
    assert inv_stage.is_completed is True
    assert inv_stage.operator_id == "OP-002"

    # Stage 3: Close Incident
    ok, msg, lc3 = command_service.transition_incident_status(
        incident_id=incident_id,
        target_status="CLOSED",
        operator_id="OP-003",
        role="SUPERVISOR",
        notes="Incident verified and addressed; closed by supervisor"
    )
    assert ok is True
    assert lc3.current_status == "CLOSED"
    cls_stage = next(s for s in lc3.stages if s.stage == "CLOSED")
    assert cls_stage.is_completed is True

    # Verify history entries
    assert len(lc3.history) == 3


def test_invalid_lifecycle_transition_rejected():
    """Tests that invalid lifecycle transitions (e.g. CLOSED -> INVESTIGATING) are rejected."""
    res = simulation_engine.run_scenario_3_confirmed_fence_crossing()
    incident_id = res["incident_id"]

    # Acknowledge first
    command_service.transition_incident_status(incident_id, "ACKNOWLEDGED")
    # Close
    command_service.transition_incident_status(incident_id, "CLOSED")

    # Now attempt invalid transition: CLOSED -> INVESTIGATING
    ok, msg, lc = command_service.transition_incident_status(
        incident_id=incident_id,
        target_status="INVESTIGATING",
        operator_id="OP-001"
    )
    assert ok is False
    assert "Invalid lifecycle transition" in msg


def test_operator_notes_persistence_and_audit():
    """Tests creating, retrieving, and auditing operator investigation notes."""
    res = simulation_engine.run_scenario_4_multi_camera_traverse()
    incident_id = res["incident_id"]

    # Add note 1
    note1 = command_service.add_incident_note(
        incident_id=incident_id,
        operator_id="OP-007",
        role="INVESTIGATOR",
        note_text="Subject observed carrying black backpack near CAM-02 boundary."
    )
    assert note1 is not None
    assert note1.operator_id == "OP-007"
    assert "black backpack" in note1.note

    # Add note 2
    note2 = command_service.add_incident_note(
        incident_id=incident_id,
        operator_id="OP-001",
        role="OPERATOR",
        note_text="Forwarded coordinates to Sector C ground patrol."
    )
    assert note2 is not None

    # Retrieve all notes
    all_notes = command_service.get_incident_notes(incident_id)
    assert len(all_notes) == 2
    assert any("black backpack" in n.note for n in all_notes)
    assert any("Sector C ground patrol" in n.note for n in all_notes)

    # Check operator actions audit trail
    actions = command_service.get_operator_actions(incident_id)
    assert len(actions) >= 2
    assert any(a.action == "ADD_NOTE" for a in actions)
