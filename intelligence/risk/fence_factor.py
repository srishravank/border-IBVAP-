from typing import Dict, Any, Optional, List
from intelligence.risk.factor_base import BaseRiskFactor, RiskFactorResult


class FenceCrossingFactor(BaseRiskFactor):
    """
    Evaluates verified boundary events (virtual fence entry, intrusion, transit)
    derived from Phase 3 multi-frame verification.
    """

    @property
    def factor_type(self) -> str:
        return "FENCE_CROSSING"

    @property
    def default_weight(self) -> float:
        return 25.0

    def evaluate(self, incident_context: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> RiskFactorResult:
        events = incident_context.get("events", [])

        if not events:
            return RiskFactorResult(
                factor_type=self.factor_type,
                factor_name="Virtual Fence Crossing",
                raw_score=0.0,
                confidence=1.0,
                evidence="No virtual fence boundary crossings detected.",
                source_event_ids=[],
                metadata={"boundary_event_count": 0}
            )

        event_severities = {
            "ZONE_INTRUSION": 1.0,
            "VIRTUAL_FENCE_CROSSING": 1.0,
            "ZONE_ENTRY": 0.8,
            "ZONE_EXIT": 0.4,
            "APPROACHING": 0.2
        }

        max_severity = 0.0
        boundary_actions = []
        source_event_ids = []
        confidences = []

        for evt in events:
            evt_id = getattr(evt, "event_id", None) or (evt.get("event_id") if isinstance(evt, dict) else "")
            etype = getattr(evt, "event_type", "") or (evt.get("event_type", "") if isinstance(evt, dict) else "")
            zname = getattr(evt, "zone_name", "") or (evt.get("zone_name", "") if isinstance(evt, dict) else "")
            e_status = getattr(evt, "status", "CONFIRMED") if hasattr(evt, "status") else evt.get("status", "CONFIRMED")
            evt_conf = getattr(evt, "confidence", 1.0) if hasattr(evt, "confidence") else evt.get("confidence", 1.0)

            # Only consider CONFIRMED or VERIFIED events
            if e_status not in ("CONFIRMED", "VERIFYING"):
                continue

            if evt_id and evt_id not in source_event_ids:
                source_event_ids.append(evt_id)
            confidences.append(evt_conf)

            sev = event_severities.get(etype.upper(), 0.5)
            if sev > max_severity:
                max_severity = sev

            action_desc = f"{etype} at {zname or 'boundary'}"
            if action_desc not in boundary_actions:
                boundary_actions.append(action_desc)

        avg_conf = sum(confidences) / len(confidences) if confidences else 1.0

        if max_severity >= 1.0:
            evidence_text = f"Confirmed crossing of configured restricted-zone virtual fence ({', '.join(boundary_actions)})."
        elif max_severity >= 0.8:
            evidence_text = f"Confirmed entry through configured boundary corridor ({', '.join(boundary_actions)})."
        elif max_severity >= 0.4:
            evidence_text = f"Boundary transition observed ({', '.join(boundary_actions)})."
        else:
            evidence_text = "No critical boundary crossings recorded."

        return RiskFactorResult(
            factor_type=self.factor_type,
            factor_name="Virtual Fence Crossing",
            raw_score=round(max_severity, 3),
            confidence=round(avg_conf, 3),
            evidence=evidence_text,
            source_event_ids=source_event_ids,
            metadata={
                "max_severity": max_severity,
                "boundary_actions": boundary_actions
            }
        )
