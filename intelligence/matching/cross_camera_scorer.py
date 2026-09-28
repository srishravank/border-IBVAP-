from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

from backend.config import settings
from intelligence.matching.appearance_matcher import BaseAppearanceMatcher, HistogramAppearanceMatcher
from intelligence.matching.temporal_matcher import TemporalMatcher
from intelligence.matching.trajectory_matcher import TrajectoryMatcher
from intelligence.topology.camera_topology import CameraTopologyGraph, CameraRelation


@dataclass
class MatchScoreBreakdown:
    match_score: float
    match_status: str  # NO_MATCH, POSSIBLE_MATCH, LIKELY_MATCH, CONFIRMED_LINK
    appearance_score: float
    temporal_score: float
    topology_score: float
    trajectory_score: float
    factors: List[str] = field(default_factory=list)
    time_delta_seconds: float = 0.0


class CrossCameraScorer:
    """
    Computes multi-factor cross-camera subject matching scores with transparent evidence factors.
    Combines Appearance, Temporal, Topology, and Trajectory signals.
    """

    def __init__(
        self,
        appearance_matcher: Optional[BaseAppearanceMatcher] = None,
        temporal_matcher: Optional[TemporalMatcher] = None,
        trajectory_matcher: Optional[TrajectoryMatcher] = None
    ):
        self.appearance_matcher = appearance_matcher or HistogramAppearanceMatcher()
        self.temporal_matcher = temporal_matcher or TemporalMatcher()
        self.trajectory_matcher = trajectory_matcher or TrajectoryMatcher()

    def evaluate_match(
        self,
        obs_a: dict,  # Origin observation / track metadata
        obs_b: dict,  # Destination observation / track metadata
        topology: CameraTopologyGraph,
        weights: Optional[Dict[str, float]] = None
    ) -> MatchScoreBreakdown:
        """
        Evaluates candidate match between two entity observations across cameras.

        obs dictionary expected keys:
        - camera_id: str
        - track_id: int
        - object_type: str ('person', 'vehicle')
        - timestamp: str | datetime
        - appearance_vector / crop: Optional
        - trajectory: List[[x, y]]
        """
        w = weights or {
            "appearance": settings.APPEARANCE_WEIGHT,
            "temporal": settings.TEMPORAL_WEIGHT,
            "topology": settings.TOPOLOGY_WEIGHT,
            "trajectory": settings.TRAJECTORY_WEIGHT,
        }

        factors = []

        # 1. Object Class Compatibility Gate
        type_a = obs_a.get("object_type", "person")
        type_b = obs_b.get("object_type", "person")
        if type_a != type_b:
            return MatchScoreBreakdown(
                match_score=0.0,
                match_status="NO_MATCH",
                appearance_score=0.0,
                temporal_score=0.0,
                topology_score=0.0,
                trajectory_score=0.0,
                factors=[f"Object class mismatch ({type_a} != {type_b})"],
                time_delta_seconds=0.0
            )
        factors.append(f"Matching object class ({type_a})")

        cam_a = obs_a.get("camera_id", "")
        cam_b = obs_b.get("camera_id", "")

        # 2. Camera Topology Route Gate
        rel = topology.get_relation(cam_a, cam_b)
        if cam_a == cam_b:
            topo_score = 1.0
            min_sec, max_sec = 0.0, 3600.0
            factors.append(f"Same camera tracking continuity ({cam_a})")
        elif rel is not None and rel.enabled:
            topo_score = 1.0
            min_sec = rel.min_transition_seconds
            max_sec = rel.max_transition_seconds
            factors.append(f"Valid topology route ({cam_a} -> {cam_b}, distance ~{rel.distance_meters:.0f}m)")
        else:
            topo_score = 0.20
            min_sec = settings.MIN_TRANSITION_SECONDS
            max_sec = settings.MAX_TRANSITION_SECONDS
            factors.append(f"Unconnected or distant topology route ({cam_a} -> {cam_b})")

        # 3. Temporal Compatibility
        time_a = obs_a.get("timestamp", "")
        time_b = obs_b.get("timestamp", "")
        temp_score, time_delta, temp_reason = self.temporal_matcher.evaluate_transit(
            time_a, time_b, min_seconds=min_sec, max_seconds=max_sec
        )
        factors.append(temp_reason)

        # 4. Appearance Feature Similarity
        feat_a = obs_a.get("appearance_vector")
        feat_b = obs_b.get("appearance_vector")
        if feat_a is None and "crop" in obs_a:
            feat_a = self.appearance_matcher.extract_features(obs_a.get("crop"), obs_a)
        if feat_b is None and "crop" in obs_b:
            feat_b = self.appearance_matcher.extract_features(obs_b.get("crop"), obs_b)

        if feat_a is not None and feat_b is not None:
            app_score = self.appearance_matcher.compute_similarity(feat_a, feat_b)
            if app_score >= 0.80:
                factors.append(f"High appearance similarity ({app_score * 100:.1f}%)")
            elif app_score >= 0.55:
                factors.append(f"Moderate appearance similarity ({app_score * 100:.1f}%)")
            else:
                factors.append(f"Weak appearance similarity ({app_score * 100:.1f}%)")
        else:
            # Fallback when visual crops are not present (e.g. synthetic test)
            app_score = 0.75
            factors.append("Default visual consistency baseline (no crop available)")

        # 5. Trajectory Heading Compatibility
        traj_a = obs_a.get("trajectory", [])
        traj_b = obs_b.get("trajectory", [])
        traj_score, traj_reason = self.trajectory_matcher.evaluate_trajectory_compatibility(
            traj_a, traj_b
        )
        factors.append(traj_reason)

        # Composite Weighted Score
        composite_score = (
            w["appearance"] * app_score +
            w["temporal"] * temp_score +
            w["topology"] * topo_score +
            w["trajectory"] * traj_score
        )
        composite_score = round(max(0.0, min(1.0, composite_score)), 3)

        # Categorize Match Status
        if composite_score >= settings.CROSS_CAMERA_MATCH_THRESHOLD:
            status = "CONFIRMED_LINK"
        elif composite_score >= 0.65:
            status = "LIKELY_MATCH"
        elif composite_score >= 0.40:
            status = "POSSIBLE_MATCH"
        else:
            status = "NO_MATCH"

        return MatchScoreBreakdown(
            match_score=composite_score,
            match_status=status,
            appearance_score=round(app_score, 3),
            temporal_score=round(temp_score, 3),
            topology_score=round(topo_score, 3),
            trajectory_score=round(traj_score, 3),
            factors=factors,
            time_delta_seconds=round(time_delta, 1)
        )
