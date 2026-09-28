from typing import Dict, Any, Optional, List
from intelligence.risk.factor_base import BaseRiskFactor, RiskFactorResult


class ZoneSensitivityFactor(BaseRiskFactor):
    """
    Evaluates the security sensitivity and classification of virtual zones
    intersected by verified incident events.
    """

    @property
    def factor_type(self) -> str:
        return "ZONE_SENSITIVITY"

    @property
    def default_weight(self) -> float:
        return 20.0

    def evaluate(self, incident_context: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> RiskFactorResult:
        events = incident_context.get("events", [])
        zones_map = incident_context.get("zones", {})

        if not events:
            return RiskFactorResult(
                factor_type=self.factor_type,
                factor_name="Zone Sensitivity",
                raw_score=0.0,
                confidence=1.0,
                evidence="No confirmed zone events detected for this incident.",
                source_event_ids=[],
                metadata={"zone_count": 0}
            )

        max_zone_score = 0.0
        contributing_zones = []
        source_event_ids = []
        confidences = []

        sensitivity_multiplier = {
            "high": 1.0,
            "medium": 0.65,
            "low": 0.30
        }

        type_multiplier = {
            "restricted": 1.0,
            "exclusion": 0.85,
            "checkpoint": 0.50,
            "buffer": 0.35
        }

        for evt in events:
            evt_id = getattr(evt, "event_id", None) or (evt.get("event_id") if isinstance(evt, dict) else "")
            zone_id = getattr(evt, "zone_id", None) or (evt.get("zone_id") if isinstance(evt, dict) else "")
            zone_name = getattr(evt, "zone_name", None) or (evt.get("zone_name") if isinstance(evt, dict) else "")
            evt_conf = getattr(evt, "confidence", 1.0) if hasattr(evt, "confidence") else evt.get("confidence", 1.0)
            
            if evt_id and evt_id not in source_event_ids:
                source_event_ids.append(evt_id)
            confidences.append(evt_conf)

            zone = zones_map.get(zone_id)
            if zone:
                sens = (getattr(zone, "sensitivity", "") or (zone.get("sensitivity", "") if isinstance(zone, dict) else "")).lower()
                ztype = (getattr(zone, "zone_type", "") or (zone.get("zone_type", "") if isinstance(zone, dict) else "")).lower()
            else:
                sens = "medium"
                ztype = "restricted"

            s_score = sensitivity_multiplier.get(sens, 0.5)
            t_score = type_multiplier.get(ztype, 0.5)
            combined_zone_score = s_score * t_score

            if combined_zone_score > max_zone_score:
                max_zone_score = combined_zone_score

            z_desc = f"{zone_name or zone_id} ({sens.upper()} sensitivity, {ztype.capitalize()})"
            if z_desc not in contributing_zones:
                contributing_zones.append(z_desc)

        avg_conf = sum(confidences) / len(confidences) if confidences else 1.0

        if max_zone_score >= 0.8:
            evidence_text = f"Activity verified within high-sensitivity restricted sector ({', '.join(contributing_zones)})."
        elif max_zone_score >= 0.5:
            evidence_text = f"Activity verified within medium-sensitivity border zone ({', '.join(contributing_zones)})."
        elif max_zone_score > 0.0:
            evidence_text = f"Activity observed within low-sensitivity buffer zone ({', '.join(contributing_zones)})."
        else:
            evidence_text = "No restricted border zones affected."

        return RiskFactorResult(
            factor_type=self.factor_type,
            factor_name="Zone Sensitivity",
            raw_score=round(max_zone_score, 3),
            confidence=round(avg_conf, 3),
            evidence=evidence_text,
            source_event_ids=source_event_ids,
            metadata={
                "max_zone_score": max_zone_score,
                "contributing_zones": contributing_zones,
                "event_count": len(events)
            }
        )
