from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from intelligence.risk.factor_base import BaseRiskFactor, RiskFactorResult
from intelligence.risk.zone_factor import ZoneSensitivityFactor
from intelligence.risk.fence_factor import FenceCrossingFactor
from intelligence.risk.night_factor import NightMovementFactor
from intelligence.risk.trajectory_factor import TrajectoryFactor
from intelligence.risk.cross_camera_factor import CrossCameraFactor
from intelligence.risk.vehicle_factor import VehicleCorrelationFactor
from intelligence.risk.behaviour_factor import BehaviourFactor
from intelligence.risk.explanation_generator import ExplanationGenerator
from backend.config import settings


@dataclass
class AggregatedRiskAssessment:
    """
    Standardized final result of the Risk Engine aggregation.
    """
    incident_id: str
    subject_id: str
    score: float                         # Normalized score in [0.0, 100.0]
    risk_level: str                      # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float                    # Overall confidence in [0.0, 1.0]
    config_version: str                  # e.g., 'v1.0.0'
    explanation: str                     # Human-readable evidence narrative
    factors: List[RiskFactorResult] = field(default_factory=list)
    evidence_checklist: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class RiskAggregator:
    """
    Central Risk Aggregator for IBVAP 2.0 (Phase 5).
    Coordinates modular factor evaluation, applies versioned weights,
    normalizes output to [0, 100], assigns risk levels, and generates explainability metadata.
    """

    def __init__(self):
        self.factors: Dict[str, BaseRiskFactor] = {
            "ZONE_SENSITIVITY": ZoneSensitivityFactor(),
            "FENCE_CROSSING": FenceCrossingFactor(),
            "NIGHT_MOVEMENT": NightMovementFactor(),
            "TRAJECTORY": TrajectoryFactor(),
            "CROSS_CAMERA_JOURNEY": CrossCameraFactor(),
            "RELATED_VEHICLE_ACTIVITY": VehicleCorrelationFactor(),
            "BEHAVIOURAL_ANOMALY": BehaviourFactor()
        }

    def assess_incident(
        self,
        incident_context: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> AggregatedRiskAssessment:
        """
        Executes end-to-end explainable risk assessment for a verified incident.
        """
        cfg = config or {}
        config_version = cfg.get("config_version", "v1.0.0")
        weights = cfg.get("weights", {
            "zone": settings.RISK_WEIGHT_ZONE,
            "fence": settings.RISK_WEIGHT_FENCE,
            "night": settings.RISK_WEIGHT_NIGHT,
            "trajectory": settings.RISK_WEIGHT_TRAJECTORY,
            "cross_camera": settings.RISK_WEIGHT_CROSS_CAMERA,
            "vehicle": settings.RISK_WEIGHT_VEHICLE,
            "behaviour": settings.RISK_WEIGHT_BEHAVIOUR
        })
        thresholds = cfg.get("thresholds", {
            "low_max": settings.RISK_LOW_MAX,
            "medium_max": settings.RISK_MEDIUM_MAX,
            "high_max": settings.RISK_HIGH_MAX
        })
        enabled_factors = cfg.get("enabled_factors", [
            "ZONE_SENSITIVITY",
            "FENCE_CROSSING",
            "NIGHT_MOVEMENT",
            "TRAJECTORY",
            "CROSS_CAMERA_JOURNEY",
            "RELATED_VEHICLE_ACTIVITY"
        ])

        # Map weight keys to factor types
        weight_key_map = {
            "ZONE_SENSITIVITY": weights.get("zone", 20.0),
            "FENCE_CROSSING": weights.get("fence", 25.0),
            "NIGHT_MOVEMENT": weights.get("night", 15.0),
            "TRAJECTORY": weights.get("trajectory", 15.0),
            "CROSS_CAMERA_JOURNEY": weights.get("cross_camera", 10.0),
            "RELATED_VEHICLE_ACTIVITY": weights.get("vehicle", 10.0),
            "BEHAVIOURAL_ANOMALY": weights.get("behaviour", 5.0)
        }

        incident = incident_context.get("incident")
        incident_id = getattr(incident, "incident_id", None) or (incident.get("incident_id") if isinstance(incident, dict) else "INC-UNKNOWN")
        subject_id = getattr(incident, "subject_id", None) or (incident.get("subject_id") if isinstance(incident, dict) else "SUBJ-UNKNOWN")

        factor_results: List[RiskFactorResult] = []
        total_score = 0.0
        max_possible_weight = 0.0
        confidences: List[Tuple[float, float]] = []  # (confidence, weight)

        for factor_type, factor_impl in self.factors.items():
            assigned_weight = float(weight_key_map.get(factor_type, factor_impl.default_weight))
            is_enabled = factor_type in enabled_factors

            if not is_enabled:
                res = RiskFactorResult(
                    factor_type=factor_type,
                    factor_name=factor_impl.factor_type.replace("_", " ").title(),
                    raw_score=0.0,
                    contribution=0.0,
                    confidence=1.0,
                    evidence="Factor disabled in current active risk configuration.",
                    source_event_ids=[],
                    is_available=False
                )
                factor_results.append(res)
                continue

            try:
                # Evaluate individual factor
                res = factor_impl.evaluate(incident_context, cfg)
                res.contribution = round(res.raw_score * assigned_weight, 2)
                factor_results.append(res)

                if res.is_available:
                    total_score += res.contribution
                    max_possible_weight += assigned_weight
                    confidences.append((res.confidence, assigned_weight))

            except Exception as e:
                # Failure isolation: graceful fallback if one factor fails
                res = RiskFactorResult(
                    factor_type=factor_type,
                    factor_name=factor_impl.factor_type.replace("_", " ").title(),
                    raw_score=0.0,
                    contribution=0.0,
                    confidence=0.5,
                    evidence=f"Factor evaluation temporarily unavailable: {str(e)}",
                    source_event_ids=[],
                    is_available=False,
                    metadata={"error": str(e)}
                )
                factor_results.append(res)

        # Normalize score to [0.0, 100.0]
        if max_possible_weight > 0 and max_possible_weight != 100.0:
            normalized_score = min(100.0, max(0.0, (total_score / max_possible_weight) * 100.0))
        else:
            normalized_score = min(100.0, max(0.0, total_score))

        normalized_score = round(normalized_score, 1)

        # Determine Risk Level
        low_max = float(thresholds.get("low_max", 30.0))
        med_max = float(thresholds.get("medium_max", 65.0))

        if normalized_score <= low_max:
            risk_level = "LOW"
        elif normalized_score <= med_max:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        # Calculate weighted average confidence
        total_conf_weight = sum(w for _, w in confidences)
        if total_conf_weight > 0:
            overall_confidence = round(sum(c * w for c, w in confidences) / total_conf_weight, 3)
        else:
            overall_confidence = 1.0

        # Generate Human-Readable Narrative & Evidence Checklist
        explanation = ExplanationGenerator.generate_explanation(
            incident_id=incident_id,
            subject_id=subject_id,
            score=normalized_score,
            risk_level=risk_level,
            factors=factor_results
        )
        checklist = ExplanationGenerator.generate_evidence_checklist(factor_results)

        return AggregatedRiskAssessment(
            incident_id=incident_id,
            subject_id=subject_id,
            score=normalized_score,
            risk_level=risk_level,
            confidence=overall_confidence,
            config_version=config_version,
            explanation=explanation,
            factors=factor_results,
            evidence_checklist=checklist,
            metadata={
                "total_factors_evaluated": len(factor_results),
                "active_factors_count": len([f for f in factor_results if f.is_available and f.contribution > 0]),
                "unnormalized_sum": round(total_score, 2),
                "max_weight_sum": round(max_possible_weight, 2)
            }
        )
