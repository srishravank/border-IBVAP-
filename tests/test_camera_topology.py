import pytest
from intelligence.topology.camera_topology import CameraTopologyGraph, CameraRelation


def test_camera_topology_creation_and_bidirectional():
    graph = CameraTopologyGraph()
    rel = CameraRelation(
        relation_id="TOPO-01-02",
        source_camera="CAM-01",
        destination_camera="CAM-02",
        min_transition_seconds=5.0,
        max_transition_seconds=60.0,
        distance_meters=30.0,
        direction="bidirectional",
        enabled=True
    )
    graph.add_relation(rel)

    assert graph.is_connected("CAM-01", "CAM-02") is True
    assert graph.is_connected("CAM-02", "CAM-01") is True
    assert graph.is_connected("CAM-01", "CAM-03") is False

    # Ancestor lookups
    ancestors = graph.get_candidate_ancestors("CAM-02")
    assert "CAM-01" in ancestors


def test_camera_topology_unidirectional():
    graph = CameraTopologyGraph()
    rel = CameraRelation(
        relation_id="TOPO-01-03",
        source_camera="CAM-01",
        destination_camera="CAM-03",
        min_transition_seconds=10.0,
        max_transition_seconds=120.0,
        direction="forward",
        enabled=True
    )
    graph.add_relation(rel)

    assert graph.is_connected("CAM-01", "CAM-03") is True
    assert graph.is_connected("CAM-03", "CAM-01") is False


def test_camera_topology_disabled_relation():
    graph = CameraTopologyGraph()
    rel = CameraRelation(
        relation_id="TOPO-03-04",
        source_camera="CAM-03",
        destination_camera="CAM-04",
        enabled=False
    )
    graph.add_relation(rel)

    assert graph.is_connected("CAM-03", "CAM-04") is False
