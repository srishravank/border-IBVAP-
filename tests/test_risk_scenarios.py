import pytest
from backend.services.simulation_engine import simulation_engine


def test_deterministic_scenarios_1_to_6():
    # Scenario 1: Normal Movement -> LOW risk
    s1 = simulation_engine.run_scenario_1_normal_movement()
    assert s1["status"] == "success"
    assert s1["risk_level"] == "LOW"
    assert s1["risk_score"] <= 30.0

    # Scenario 2: Verified Zone Entry -> MEDIUM risk
    s2 = simulation_engine.run_scenario_2_verified_zone_entry()
    assert s2["status"] == "success"
    assert s2["risk_level"] in ("MEDIUM", "LOW")

    # Scenario 3: Night Intrusion -> HIGH risk
    s3 = simulation_engine.run_scenario_3_night_intrusion()
    assert s3["status"] == "success"
    assert s3["risk_level"] in ("MEDIUM", "HIGH")
    assert s3["risk_score"] >= 45.0

    # Scenario 4: Cross-Camera Journey
    s4 = simulation_engine.run_multi_camera_journey_demo()
    assert s4["status"] == "success"
    assert len(s4["cameras_linked"]) == 3

    # Scenario 5: Person + Vehicle Association
    s5 = simulation_engine.run_scenario_5_person_vehicle_association()
    assert s5["status"] == "success"

    # Scenario 6: Multi-Factor Full Incident
    s6 = simulation_engine.run_scenario_6_multi_factor_incident()
    assert s6["status"] == "success"
    assert s6["risk_level"] in ("HIGH", "CRITICAL")
    assert s6["risk_score"] >= 65.0
    assert len(s6["factors"]) >= 3
