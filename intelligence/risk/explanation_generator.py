from typing import List, Dict, Any
from intelligence.risk.factor_base import RiskFactorResult


class ExplanationGenerator:
    """
    Generates human-readable, evidence-grounded textual explanations for risk assessments.
    Strictly avoids unsupported assertions, speculative intent, or black-box reasoning.
    """

    @staticmethod
    def generate_explanation(
        incident_id: str,
        subject_id: str,
        score: float,
        risk_level: str,
        factors: List[RiskFactorResult]
    ) -> str:
        """
        Synthesizes active factor results into a cohesive, explainable narrative.
        """
        significant_factors = [f for f in factors if f.is_available and f.contribution >= 5.0]

        if not significant_factors:
            return (
                f"Risk assessment for Incident '{incident_id}' (Subject '{subject_id}') is {risk_level} "
                f"with a score of {score:.0f}/100. No verified high-risk boundary, time-window, or topological anomalies detected."
            )

        # Build factor justification clauses
        clauses = []
        for f in sorted(significant_factors, key=lambda x: x.contribution, reverse=True):
            if f.factor_type == "ZONE_SENSITIVITY":
                clauses.append("verified activity occurred in a configured sensitive zone")
            elif f.factor_type == "FENCE_CROSSING":
                clauses.append("included a confirmed virtual-fence boundary crossing")
            elif f.factor_type == "NIGHT_MOVEMENT":
                clauses.append("occurred during the configured night-time surveillance period")
            elif f.factor_type == "CROSS_CAMERA_JOURNEY":
                clauses.append("exhibited persistent correlation across multiple camera sectors")
            elif f.factor_type == "RELATED_VEHICLE_ACTIVITY":
                clauses.append("associated with nearby vehicle activity in close spatial/temporal proximity")
            elif f.factor_type == "TRAJECTORY":
                clauses.append("demonstrated continuous directional movement trajectory")
            elif f.factor_type == "BEHAVIOURAL_ANOMALY":
                clauses.append("triggered behavioral anomaly criteria")

        narrative = (
            f"Risk assessment is {risk_level} (Score: {score:.0f}/100) because the verified incident "
            f"{', '.join(clauses)}."
        )

        return narrative

    @staticmethod
    def generate_evidence_checklist(factors: List[RiskFactorResult]) -> List[Dict[str, Any]]:
        """
        Builds structured factual checklist separating verified facts from risk assessment impact.
        """
        checklist = []
        for f in factors:
            if not f.is_available:
                continue

            impact_level = "ELEVATED" if f.contribution >= 15.0 else ("MODERATE" if f.contribution >= 5.0 else "NEUTRAL")
            checklist.append({
                "factor_type": f.factor_type,
                "factor_name": f.factor_name,
                "fact": f.evidence,
                "assessment": f"+{f.contribution:.1f} pts ({impact_level} impact)",
                "contribution": f.contribution,
                "confidence": f.confidence,
                "source_events": f.source_event_ids
            })
        return checklist
