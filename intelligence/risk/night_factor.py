from typing import Dict, Any, Optional, List
from datetime import datetime, time, timezone
from intelligence.risk.factor_base import BaseRiskFactor, RiskFactorResult
from backend.config import settings


def is_time_in_night_window(dt: datetime, start_str: str = "20:00", end_str: str = "05:00") -> bool:
    """
    Checks if datetime occurs within a night window (e.g. 20:00 to 05:00).
    Properly handles wrap-around across midnight.
    """
    try:
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))
        start_t = time(sh, sm)
        end_t = time(eh, em)
        target_t = dt.time()

        if start_t <= end_t:
            return start_t <= target_t <= end_t
        else:
            # Wraps past midnight (e.g. 20:00 to 05:00)
            return target_t >= start_t or target_t <= end_t
    except Exception:
        return False


class NightMovementFactor(BaseRiskFactor):
    """
    Evaluates whether verified border activity occurred during the configured
    night-time surveillance window.
    Strictly reports neutral factual time window observation without inferring intent.
    """

    @property
    def factor_type(self) -> str:
        return "NIGHT_MOVEMENT"

    @property
    def default_weight(self) -> float:
        return 15.0

    def evaluate(self, incident_context: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> RiskFactorResult:
        night_start = (config or {}).get("night_start_time", settings.NIGHT_START_TIME)
        night_end = (config or {}).get("night_end_time", settings.NIGHT_END_TIME)

        events = incident_context.get("events", [])
        journey = incident_context.get("journey", [])
        incident = incident_context.get("incident")

        timestamps: List[datetime] = []
        source_event_ids: List[str] = []

        # Collect event timestamps
        for evt in events:
            evt_id = getattr(evt, "event_id", None) or (evt.get("event_id") if isinstance(evt, dict) else "")
            ts = getattr(evt, "created_at", None) or (evt.get("created_at") if isinstance(evt, dict) else None)
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except Exception:
                    ts = None
            if isinstance(ts, datetime):
                timestamps.append(ts)
                if evt_id and evt_id not in source_event_ids:
                    source_event_ids.append(evt_id)

        # Collect journey timestamps
        for step in journey:
            ts = getattr(step, "first_timestamp", None) or (step.get("first_timestamp") if isinstance(step, dict) else None)
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except Exception:
                    ts = None
            if isinstance(ts, datetime):
                timestamps.append(ts)

        # Check incident timestamp fallback
        if not timestamps and incident:
            ts = getattr(incident, "created_at", None) or (incident.get("created_at") if isinstance(incident, dict) else None)
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except Exception:
                    ts = None
            if isinstance(ts, datetime):
                timestamps.append(ts)

        if not timestamps:
            return RiskFactorResult(
                factor_type=self.factor_type,
                factor_name="Night-Time Movement",
                raw_score=0.0,
                confidence=1.0,
                evidence="No timestamped activity available for night-window analysis.",
                source_event_ids=[],
                metadata={"night_window": f"{night_start} - {night_end}"}
            )

        # Check if any timestamp falls within night window
        night_events_count = sum(1 for t in timestamps if is_time_in_night_window(t, night_start, night_end))
        is_night = night_events_count > 0

        if is_night:
            raw_score = 1.0
            evidence_text = f"Confirmed activity occurred during configured night period ({night_start}–{night_end})."
        else:
            raw_score = 0.0
            evidence_text = f"Activity verified during standard daylight operational hours (outside {night_start}–{night_end})."

        return RiskFactorResult(
            factor_type=self.factor_type,
            factor_name="Night-Time Movement",
            raw_score=raw_score,
            confidence=1.0,
            evidence=evidence_text,
            source_event_ids=source_event_ids,
            metadata={
                "is_night": is_night,
                "night_start": night_start,
                "night_end": night_end,
                "night_events_ratio": round(night_events_count / max(1, len(timestamps)), 2)
            }
        )
