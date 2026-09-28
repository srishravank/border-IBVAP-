from typing import Dict, Any, Optional, List
from intelligence.risk.factor_base import BaseRiskFactor, RiskFactorResult


class VehicleCorrelationFactor(BaseRiskFactor):
    """
    Evaluates contextual spatial and temporal proximity between person and vehicle entities.
    Maintains strictly neutral language ('related vehicle activity', 'spatial/temporal association')
    without inferring intent or criminal collusion.
    """

    @property
    def factor_type(self) -> str:
        return "RELATED_VEHICLE_ACTIVITY"

    @property
    def default_weight(self) -> float:
        return 10.0

    def evaluate(self, incident_context: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> RiskFactorResult:
        vehicles = incident_context.get("associated_vehicles", [])

        if not vehicles:
            return RiskFactorResult(
                factor_type=self.factor_type,
                factor_name="Related Vehicle Activity",
                raw_score=0.0,
                confidence=1.0,
                evidence="No co-located or temporally correlated vehicle activity detected.",
                source_event_ids=[],
                metadata={"vehicle_count": 0}
            )

        veh_summaries = []
        min_distance = 999.0

        for v in vehicles:
            veh_id = getattr(v, "vehicle_subject_id", None) or (v.get("vehicle_subject_id") if isinstance(v, dict) else "VEH-?")
            cam = getattr(v, "camera_id", None) or (v.get("camera_id") if isinstance(v, dict) else "")
            dist = getattr(v, "proximity_meters", 10.0) if hasattr(v, "proximity_meters") else v.get("proximity_meters", 10.0)
            
            if dist < min_distance:
                min_distance = dist
            veh_summaries.append(f"{veh_id} on {cam} (~{dist:.0f}m)")

        if min_distance <= 5.0:
            raw_score = 1.0
            evidence_text = f"Vehicle observed in immediate physical proximity to subject ({', '.join(veh_summaries)})."
        elif min_distance <= 15.0:
            raw_score = 0.8
            evidence_text = f"Vehicle spatially and temporally associated with subject ({', '.join(veh_summaries)})."
        else:
            raw_score = 0.5
            evidence_text = f"Co-occurring vehicle activity observed in sector ({', '.join(veh_summaries)})."

        return RiskFactorResult(
            factor_type=self.factor_type,
            factor_name="Related Vehicle Activity",
            raw_score=round(raw_score, 3),
            confidence=0.90,
            evidence=evidence_text,
            source_event_ids=[],
            metadata={
                "vehicle_count": len(vehicles),
                "vehicles": veh_summaries,
                "min_proximity_meters": min_distance
            }
        )
