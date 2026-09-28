from typing import Dict, Any, Optional, List
from intelligence.risk.factor_base import BaseRiskFactor, RiskFactorResult


class CrossCameraFactor(BaseRiskFactor):
    """
    Evaluates multi-camera journey continuity and transit breadth along the border perimeter.
    Provides contextual topological evidence without assuming intent.
    """

    @property
    def factor_type(self) -> str:
        return "CROSS_CAMERA_JOURNEY"

    @property
    def default_weight(self) -> float:
        return 10.0

    def evaluate(self, incident_context: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> RiskFactorResult:
        journey = incident_context.get("journey", [])
        subject = incident_context.get("subject")

        visited_cams: List[str] = []
        confirmed_links = 0
        total_links = 0
        scores: List[float] = []

        for step in journey:
            cam = getattr(step, "camera_id", None) or (step.get("camera_id") if isinstance(step, dict) else "")
            m_status = getattr(step, "match_status", "") or (step.get("match_status", "") if isinstance(step, dict) else "")
            score = getattr(step, "match_score", 1.0) if hasattr(step, "match_score") else step.get("match_score", 1.0)

            if cam and cam not in visited_cams:
                visited_cams.append(cam)
            if m_status == "CONFIRMED_LINK":
                confirmed_links += 1
            scores.append(score)
            total_links += 1

        cam_count = len(visited_cams)
        if cam_count == 0 and subject:
            cam_count = getattr(subject, "total_cameras_visited", 1) if hasattr(subject, "total_cameras_visited") else subject.get("total_cameras_visited", 1)

        avg_score = sum(scores) / len(scores) if scores else 1.0

        if cam_count >= 3:
            raw_score = 1.0
            evidence_text = f"Subject tracked across {cam_count} connected camera sectors ({' → '.join(visited_cams)}) along border corridor."
        elif cam_count == 2:
            raw_score = 0.7
            evidence_text = f"Subject observed transitioning across 2 connected camera sectors ({' → '.join(visited_cams)})."
        else:
            raw_score = 0.2
            evidence_text = f"Activity localized to single camera sector ({visited_cams[0] if visited_cams else 'initial camera'})."

        return RiskFactorResult(
            factor_type=self.factor_type,
            factor_name="Cross-Camera Transit",
            raw_score=round(raw_score, 3),
            confidence=round(avg_score, 3),
            evidence=evidence_text,
            source_event_ids=[],
            metadata={
                "camera_count": cam_count,
                "visited_cameras": visited_cams,
                "confirmed_links": confirmed_links
            }
        )
