import pytest
import numpy as np
from datetime import datetime, timezone, timedelta

from intelligence.matching.appearance_matcher import HistogramAppearanceMatcher
from intelligence.matching.temporal_matcher import TemporalMatcher
from intelligence.matching.trajectory_matcher import TrajectoryMatcher
from intelligence.matching.cross_camera_scorer import CrossCameraScorer
from intelligence.topology.camera_topology import CameraTopologyGraph, CameraRelation


def test_appearance_matcher_similarity():
    matcher = HistogramAppearanceMatcher()

    # Identical synthetic feature vectors
    vec_a = np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float32)
    vec_b = np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float32)
    sim = matcher.compute_similarity(vec_a, vec_b)
    assert sim >= 0.99

    # Orthogonal vectors
    vec_c = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    vec_d = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
    sim_ortho = matcher.compute_similarity(vec_c, vec_d)
    assert sim_ortho <= 0.10


def test_temporal_matcher_transit_windows():
    matcher = TemporalMatcher()
    t0 = datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc)

    # 1. Optimal window (30 seconds for 5-60s window)
    t1 = t0 + timedelta(seconds=30)
    score, delta, reason = matcher.evaluate_transit(t0, t1, min_seconds=5.0, max_seconds=60.0)
    assert delta == 30.0
    assert score >= 0.85

    # 2. Too fast (2 seconds < 5s min)
    t_fast = t0 + timedelta(seconds=2)
    score_fast, delta_fast, reason_fast = matcher.evaluate_transit(t0, t_fast, min_seconds=5.0, max_seconds=60.0)
    assert delta_fast == 2.0
    assert score_fast < 0.35

    # 3. Expired / Too slow (300 seconds > 60s max)
    t_slow = t0 + timedelta(seconds=300)
    score_slow, delta_slow, reason_slow = matcher.evaluate_transit(t0, t_slow, min_seconds=5.0, max_seconds=60.0)
    assert score_slow < 0.10


def test_trajectory_matcher_heading():
    matcher = TrajectoryMatcher()

    # Parallel forward trajectories
    traj_a = [[100.0, 100.0], [150.0, 100.0], [200.0, 100.0]]  # Moving +X
    traj_b = [[50.0, 100.0], [100.0, 100.0], [150.0, 100.0]]   # Moving +X
    score, reason = matcher.evaluate_trajectory_compatibility(traj_a, traj_b)
    assert score >= 0.90

    # Opposite direction trajectories
    traj_rev = [[200.0, 100.0], [150.0, 100.0], [100.0, 100.0]] # Moving -X
    score_rev, reason_rev = matcher.evaluate_trajectory_compatibility(traj_a, traj_rev)
    assert score_rev <= 0.50


def test_cross_camera_scorer_composite():
    scorer = CrossCameraScorer()
    graph = CameraTopologyGraph()
    graph.add_relation(CameraRelation(
        relation_id="TOPO-01-02",
        source_camera="CAM-01",
        destination_camera="CAM-02",
        min_transition_seconds=5.0,
        max_transition_seconds=60.0,
        distance_meters=40.0
    ))

    t0 = datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(seconds=20)
    feat = [0.8, 0.2, 0.1, 0.5] * 10

    obs_a = {
        "camera_id": "CAM-01",
        "track_id": 10,
        "object_type": "person",
        "timestamp": t0.isoformat(),
        "appearance_vector": feat,
        "trajectory": [[100.0, 200.0], [200.0, 200.0]]
    }

    obs_b = {
        "camera_id": "CAM-02",
        "track_id": 20,
        "object_type": "person",
        "timestamp": t1.isoformat(),
        "appearance_vector": feat,
        "trajectory": [[150.0, 200.0], [250.0, 200.0]]
    }

    # Compatible match
    result = scorer.evaluate_match(obs_a, obs_b, graph)
    assert result.match_score >= 0.75
    assert result.match_status in ("CONFIRMED_LINK", "LIKELY_MATCH")
    assert len(result.factors) >= 4

    # Object class mismatch test
    obs_vehicle = dict(obs_b)
    obs_vehicle["object_type"] = "vehicle"
    mismatch_res = scorer.evaluate_match(obs_a, obs_vehicle, graph)
    assert mismatch_res.match_score == 0.0
    assert mismatch_res.match_status == "NO_MATCH"
