import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.connection import init_db
from backend.services.simulation_engine import simulation_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    simulation_engine.reset_simulation()
    yield
    simulation_engine.reset_simulation()


def test_topology_api_crud():
    # 1. GET topology
    res = client.get("/api/cameras/topology")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 3

    # 2. POST create topology relation
    payload = {
        "source_camera": "CAM-01",
        "destination_camera": "CAM-04",
        "min_transition_seconds": 15.0,
        "max_transition_seconds": 240.0,
        "distance_meters": 120.0,
        "direction": "bidirectional",
        "enabled": True,
        "description": "Direct outpost express route."
    }
    create_res = client.post("/api/cameras/topology", json=payload)
    assert create_res.status_code == 200
    created_data = create_res.json()
    assert created_data["relation_id"] == "TOPO-CAM-01-CAM-04"


def test_subjects_and_journey_api():
    # Run demo simulation first
    sim_res = client.post("/api/demo/cross-camera/journey")
    assert sim_res.status_code == 200
    subj_id = sim_res.json()["subject_id"]

    # 1. GET /api/subjects
    subjs_res = client.get("/api/subjects")
    assert subjs_res.status_code == 200
    assert len(subjs_res.json()) > 0

    # 2. GET /api/subjects/{id}/journey
    journey_res = client.get(f"/api/subjects/{subj_id}/journey")
    assert journey_res.status_code == 200
    j_data = journey_res.json()
    assert j_data["total_cameras"] == 3
    assert len(j_data["journey_steps"]) == 3


def test_incidents_timeline_and_graph_api():
    client.post("/api/demo/cross-camera/journey")

    # 1. GET /api/incidents
    inc_res = client.get("/api/incidents")
    assert inc_res.status_code == 200
    incidents = inc_res.json()
    assert len(incidents) > 0
    inc_id = incidents[0]["incident_id"]

    # 2. GET /api/incidents/{id}/timeline
    timeline_res = client.get(f"/api/incidents/{inc_id}/timeline")
    assert timeline_res.status_code == 200
    assert len(timeline_res.json()) >= 4

    # 3. GET /api/incidents/{id}/graph
    graph_res = client.get(f"/api/incidents/{inc_id}/graph")
    assert graph_res.status_code == 200
    g_data = graph_res.json()
    assert len(g_data["nodes"]) > 0
    assert len(g_data["edges"]) > 0
