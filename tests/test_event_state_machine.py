import pytest
from verification.event_state_machine import TrackZoneStateManager
from backend.models.security_event import SecurityEventType


def test_track_zone_entry_and_exit_transitions():
    """Test: Boundary crossing generates ZONE_ENTRY on entry and ZONE_EXIT on departure."""
    mgr = TrackZoneStateManager()

    # Initial state: OUTSIDE
    assert mgr.get_state("CAM-01", 17, "ZONE-01") == "OUTSIDE"

    # Target crosses boundary into zone
    t1 = mgr.evaluate_transition("CAM-01", 17, "ZONE-01", is_currently_inside=True)
    assert t1 == SecurityEventType.ZONE_ENTRY
    assert mgr.get_state("CAM-01", 17, "ZONE-01") == "INSIDE"

    # Target stays inside zone on next frame -> No new transition
    t2 = mgr.evaluate_transition("CAM-01", 17, "ZONE-01", is_currently_inside=True)
    assert t2 is None

    # Target exits zone
    t3 = mgr.evaluate_transition("CAM-01", 17, "ZONE-01", is_currently_inside=False)
    assert t3 == SecurityEventType.ZONE_EXIT
    assert mgr.get_state("CAM-01", 17, "ZONE-01") == "OUTSIDE"


def test_duplicate_event_prevention():
    """
    Test: Once a zone intrusion is confirmed, the system deduplicates and avoids creating redundant events
    while the target remains inside the zone.
    """
    mgr = TrackZoneStateManager()

    # Target enters
    mgr.evaluate_transition("CAM-01", 10, "ZONE-01", is_currently_inside=True)
    assert mgr.is_already_confirmed("CAM-01", 10, "ZONE-01", "ZONE_INTRUSION") is False

    # Mark as confirmed
    mgr.mark_confirmed("CAM-01", 10, "ZONE-01", "ZONE_INTRUSION")
    assert mgr.is_already_confirmed("CAM-01", 10, "ZONE-01", "ZONE_INTRUSION") is True

    # Target remains inside for 50 frames -> must still report already confirmed
    for _ in range(50):
        t = mgr.evaluate_transition("CAM-01", 10, "ZONE-01", is_currently_inside=True)
        assert t is None
        assert mgr.is_already_confirmed("CAM-01", 10, "ZONE-01", "ZONE_INTRUSION") is True
