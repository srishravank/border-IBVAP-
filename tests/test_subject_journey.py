import pytest
from datetime import datetime, timezone, timedelta

from backend.database.connection import init_db, SessionLocal
from backend.services.simulation_engine import simulation_engine
from backend.services.cross_camera_engine import cross_camera_engine


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    simulation_engine.reset_simulation()
    yield
    simulation_engine.reset_simulation()


def test_deterministic_multi_camera_journey():
    res = simulation_engine.run_multi_camera_journey_demo()
    assert res["status"] == "success"

    subj_id = res["subject_id"]
    assert subj_id.startswith("SUBJ-")

    journey = cross_camera_engine.get_subject_journey(subj_id)
    assert journey is not None
    assert journey.total_cameras == 3
    assert journey.cameras_sequence == ["CAM-01", "CAM-02", "CAM-03"]

    # Verify chronological sequence of steps
    assert len(journey.journey_steps) == 3
    step1, step2, step3 = journey.journey_steps

    assert step1.camera_id == "CAM-01"
    assert step1.track_id == 17

    assert step2.camera_id == "CAM-02"
    assert step2.track_id == 42
    assert step2.match_score >= 0.75
    # Contextual vehicle associated on CAM-02
    assert len(step2.associated_vehicles) > 0

    assert step3.camera_id == "CAM-03"
    assert step3.track_id == 11
    assert step3.match_score >= 0.75


def test_false_match_rejection_scenario():
    res = simulation_engine.run_false_match_rejection_demo()
    assert res["status"] == "success"
    assert res["are_linked"] is False
    assert res["subject_cam01"] != res["subject_cam04"]
