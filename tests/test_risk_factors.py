import pytest
from datetime import datetime, timezone

from intelligence.risk.zone_factor import ZoneSensitivityFactor
from intelligence.risk.fence_factor import FenceCrossingFactor
from intelligence.risk.night_factor import NightMovementFactor, is_time_in_night_window
from intelligence.risk.trajectory_factor import TrajectoryFactor
from intelligence.risk.cross_camera_factor import CrossCameraFactor
from intelligence.risk.vehicle_factor import VehicleCorrelationFactor
from intelligence.risk.behaviour_factor import BehaviourFactor


def test_zone_sensitivity_factor():
    factor = ZoneSensitivityFactor()
    assert factor.factor_type == "ZONE_SENSITIVITY"
    assert factor.default_weight == 20.0

    # Test empty events
    res_empty = factor.evaluate({"events": [], "zones": {}})
    assert res_empty.raw_score == 0.0
    assert "No confirmed zone events" in res_empty.evidence

    # Test high sensitivity restricted zone
    high_events = [{
        "event_id": "EVT-01",
        "zone_id": "ZONE-01",
        "zone_name": "Sector A Gate",
        "confidence": 0.95
    }]
    zones_map = {
        "ZONE-01": {"sensitivity": "high", "zone_type": "restricted"}
    }
    res_high = factor.evaluate({"events": high_events, "zones": zones_map})
    assert res_high.raw_score == 1.0
    assert "high-sensitivity restricted sector" in res_high.evidence
    assert "EVT-01" in res_high.source_event_ids


def test_fence_crossing_factor():
    factor = FenceCrossingFactor()
    assert factor.factor_type == "FENCE_CROSSING"
    assert factor.default_weight == 25.0

    # Test zone intrusion
    events = [{
        "event_id": "EVT-02",
        "event_type": "ZONE_INTRUSION",
        "zone_name": "Perimeter Wire",
        "status": "CONFIRMED",
        "confidence": 0.92
    }]
    res = factor.evaluate({"events": events})
    assert res.raw_score == 1.0
    assert "Confirmed crossing of configured restricted-zone" in res.evidence
    assert "EVT-02" in res.source_event_ids


def test_night_movement_factor_and_window():
    # Test time window utility with wrap-around across midnight
    day_dt = datetime(2026, 9, 20, 14, 30, tzinfo=timezone.utc)
    night_dt1 = datetime(2026, 9, 20, 22, 15, tzinfo=timezone.utc)
    night_dt2 = datetime(2026, 9, 20, 3, 45, tzinfo=timezone.utc)

    assert not is_time_in_night_window(day_dt, "20:00", "05:00")
    assert is_time_in_night_window(night_dt1, "20:00", "05:00")
    assert is_time_in_night_window(night_dt2, "20:00", "05:00")

    factor = NightMovementFactor()
    assert factor.factor_type == "NIGHT_MOVEMENT"

    # Evaluate daytime
    res_day = factor.evaluate({"events": [{"event_id": "EVT-D", "created_at": day_dt}]})
    assert res_day.raw_score == 0.0
    assert "daylight" in res_day.evidence

    # Evaluate night-time
    res_night = factor.evaluate({"events": [{"event_id": "EVT-N", "created_at": night_dt1}]})
    assert res_night.raw_score == 1.0
    assert "night period" in res_night.evidence


def test_trajectory_factor():
    factor = TrajectoryFactor()
    assert factor.factor_type == "TRAJECTORY"

    # Test persistent trajectory with continuous points
    traj = [[100.0, 100.0], [150.0, 150.0], [200.0, 200.0], [250.0, 250.0], [300.0, 300.0]]
    res = factor.evaluate({"events": [{"event_id": "EVT-T", "trajectory": traj}]})
    assert res.raw_score >= 0.8
    assert "Persistent linear movement trajectory" in res.evidence


def test_cross_camera_factor():
    factor = CrossCameraFactor()
    assert factor.factor_type == "CROSS_CAMERA_JOURNEY"

    # 3-camera journey
    journey = [
        {"camera_id": "CAM-01", "match_status": "CONFIRMED_LINK", "match_score": 1.0},
        {"camera_id": "CAM-02", "match_status": "CONFIRMED_LINK", "match_score": 0.9},
        {"camera_id": "CAM-03", "match_status": "CONFIRMED_LINK", "match_score": 0.88}
    ]
    res = factor.evaluate({"journey": journey})
    assert res.raw_score == 1.0
    assert "3 connected camera sectors" in res.evidence


def test_vehicle_correlation_factor_neutral_phrasing():
    factor = VehicleCorrelationFactor()
    assert factor.factor_type == "RELATED_VEHICLE_ACTIVITY"

    vehicles = [{
        "vehicle_subject_id": "VEH-003",
        "camera_id": "CAM-02",
        "proximity_meters": 4.5
    }]
    res = factor.evaluate({"associated_vehicles": vehicles})
    assert res.raw_score == 1.0
    assert "immediate physical proximity" in res.evidence
    # Verify strict neutral terminology (no intent inference)
    assert "criminal" not in res.evidence.lower()
    assert "threat" not in res.evidence.lower()


def test_behaviour_factor_fallback():
    factor = BehaviourFactor()
    assert factor.factor_type == "BEHAVIOURAL_ANOMALY"

    # Disabled fallback
    res = factor.evaluate({}, config={"enabled": False})
    assert not res.is_available
    assert res.raw_score == 0.0
    assert res.contribution == 0.0
    assert "unconfigured / disabled" in res.evidence
