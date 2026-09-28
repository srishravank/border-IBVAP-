import pytest
from backend.database.connection import init_db
from backend.services.simulation_engine import simulation_engine
from backend.services.cross_camera_engine import cross_camera_engine


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    simulation_engine.reset_simulation()
    yield
    simulation_engine.reset_simulation()


def test_incident_graph_structure():
    sim_res = simulation_engine.run_multi_camera_journey_demo()
    subj_id = sim_res["subject_id"]

    incidents = cross_camera_engine.get_incidents()
    assert len(incidents) > 0
    inc_id = incidents[0].incident_id

    # Build graph
    graph = cross_camera_engine.get_incident_graph(inc_id)
    assert graph is not None
    assert graph.subject_id == subj_id

    # Verify node types present
    node_types = set([n.node_type for n in graph.nodes])
    assert "SUBJECT" in node_types
    assert "CAMERA" in node_types
    assert "TRACK" in node_types
    assert "EVENT" in node_types
    assert "VEHICLE" in node_types

    # Verify relationship edge types present
    edge_types = set([e.relationship for e in graph.edges])
    assert "OBSERVED_BY" in edge_types
    assert "MATCHED_TO" in edge_types
    assert "ASSOCIATED_WITH" in edge_types


def test_incident_timeline_chronological():
    sim_res = simulation_engine.run_multi_camera_journey_demo()
    subj_id = sim_res["subject_id"]
    inc_id = f"INC-{subj_id}"

    timeline = cross_camera_engine.get_incident_timeline(inc_id)
    assert len(timeline) >= 4

    # Verify chronological sorting
    for i in range(len(timeline) - 1):
        assert timeline[i].timestamp <= timeline[i + 1].timestamp
