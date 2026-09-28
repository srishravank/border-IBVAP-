import numpy as np
from typing import Dict, Any, Optional, List
from intelligence.risk.factor_base import BaseRiskFactor, RiskFactorResult


class TrajectoryFactor(BaseRiskFactor):
    """
    Evaluates kinematic trajectory continuity, persistence, and directional displacement
    from verified multi-frame tracking history.
    Strictly factual and observable without unverified trajectory extrapolations.
    """

    @property
    def factor_type(self) -> str:
        return "TRAJECTORY"

    @property
    def default_weight(self) -> float:
        return 15.0

    def evaluate(self, incident_context: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> RiskFactorResult:
        events = incident_context.get("events", [])
        journey = incident_context.get("journey", [])

        trajectories: List[List[List[float]]] = []
        source_event_ids: List[str] = []

        for evt in events:
            evt_id = getattr(evt, "event_id", None) or (evt.get("event_id") if isinstance(evt, dict) else "")
            traj = getattr(evt, "trajectory", None) or (evt.get("trajectory") if isinstance(evt, dict) else None)
            if traj and len(traj) >= 2:
                trajectories.append(traj)
                if evt_id and evt_id not in source_event_ids:
                    source_event_ids.append(evt_id)

        if not trajectories:
            # Check journey step count as a fallback persistence indicator
            step_count = len(journey)
            if step_count >= 2:
                return RiskFactorResult(
                    factor_type=self.factor_type,
                    factor_name="Trajectory Dynamics",
                    raw_score=0.6,
                    confidence=0.85,
                    evidence=f"Persistent multi-sensor transit observed across {step_count} camera checkpoints.",
                    source_event_ids=source_event_ids,
                    metadata={"multi_camera_steps": step_count}
                )

            return RiskFactorResult(
                factor_type=self.factor_type,
                factor_name="Trajectory Dynamics",
                raw_score=0.2,
                confidence=0.7,
                evidence="Standard local entity movement with baseline persistence.",
                source_event_ids=[],
                metadata={"trajectory_count": 0}
            )

        max_displacement = 0.0
        total_points = 0
        persistent_tracks = 0

        for traj in trajectories:
            pts = np.array(traj)
            total_points += len(pts)
            if len(pts) >= 5:
                persistent_tracks += 1
            disp = float(np.linalg.norm(pts[-1] - pts[0]))
            if disp > max_displacement:
                max_displacement = disp

        # Score based on trajectory persistence and observable displacement
        if persistent_tracks > 0 and max_displacement > 100:
            raw_score = 0.9
            evidence_text = f"Persistent linear movement trajectory detected (displacement: {max_displacement:.0f}px across {total_points} verified trajectory points)."
        elif total_points >= 4:
            raw_score = 0.6
            evidence_text = f"Continuous tracking motion observed (displacement: {max_displacement:.0f}px across verified frames)."
        else:
            raw_score = 0.3
            evidence_text = "Brief localized movement observed within camera viewport."

        return RiskFactorResult(
            factor_type=self.factor_type,
            factor_name="Trajectory Dynamics",
            raw_score=round(raw_score, 3),
            confidence=0.92,
            evidence=evidence_text,
            source_event_ids=source_event_ids,
            metadata={
                "max_displacement_px": round(max_displacement, 1),
                "total_points": total_points,
                "persistent_tracks": persistent_tracks
            }
        )
