from typing import Dict, Any, Optional
from intelligence.risk.factor_base import BaseRiskFactor, RiskFactorResult
from backend.config import settings


class BehaviourFactor(BaseRiskFactor):
    """
    Modular interface for future behavioural anomaly detection (loitering, sudden acceleration, pose).
    Gracefully returns unavailable status without fabricating anomalies or causing engine failure.
    """

    @property
    def factor_type(self) -> str:
        return "BEHAVIOURAL_ANOMALY"

    @property
    def default_weight(self) -> float:
        return 5.0

    def evaluate(self, incident_context: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> RiskFactorResult:
        enabled = (config or {}).get("enabled", settings.RISK_BEHAVIOUR_ENABLED)

        if not enabled:
            return RiskFactorResult(
                factor_type=self.factor_type,
                factor_name="Behavioural Analysis",
                raw_score=0.0,
                contribution=0.0,
                confidence=1.0,
                evidence="Behavioural anomaly analysis module is currently unconfigured / disabled.",
                source_event_ids=[],
                metadata={"status": "DISABLED", "supported_in": "Future Phase"},
                is_available=False
            )

        # If enabled in future phases, read real behavioral signals:
        behaviour_signal = incident_context.get("behaviour_signal")
        if not behaviour_signal:
            return RiskFactorResult(
                factor_type=self.factor_type,
                factor_name="Behavioural Analysis",
                raw_score=0.0,
                contribution=0.0,
                confidence=0.8,
                evidence="No behavioral anomaly signals recorded.",
                source_event_ids=[],
                metadata={"status": "NO_ANOMALY"},
                is_available=True
            )

        score = float(behaviour_signal.get("score", 0.0))
        desc = str(behaviour_signal.get("description", "Atypical movement pattern detected"))

        return RiskFactorResult(
            factor_type=self.factor_type,
            factor_name="Behavioural Analysis",
            raw_score=min(1.0, max(0.0, score)),
            confidence=0.85,
            evidence=desc,
            source_event_ids=[],
            metadata=behaviour_signal,
            is_available=True
        )
