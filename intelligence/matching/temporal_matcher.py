import math
from datetime import datetime, timezone
from typing import Tuple, Union


class TemporalMatcher:
    """
    Evaluates temporal compatibility between two observations across cameras
    based on the configured minimum and maximum transit time window.
    """

    @staticmethod
    def parse_timestamp(ts: Union[str, datetime, float, int]) -> datetime:
        """Parses various timestamp formats into a UTC datetime."""
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                return ts.replace(tzinfo=timezone.utc)
            return ts
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        if isinstance(ts, str):
            try:
                # Replace trailing Z with +00:00 for fromisoformat compatibility
                clean_ts = ts.replace("Z", "+00:00")
                return datetime.fromisoformat(clean_ts)
            except Exception:
                return datetime.now(timezone.utc)
        return datetime.now(timezone.utc)

    def evaluate_transit(
        self,
        time_a: Union[str, datetime, float],
        time_b: Union[str, datetime, float],
        min_seconds: float = 5.0,
        max_seconds: float = 120.0
    ) -> Tuple[float, float, str]:
        """
        Calculates the time difference and evaluates temporal compatibility.

        Returns:
            (score, delta_seconds, reason)
            - score: [0.0, 1.0] where 1.0 is optimal transit time within the window.
            - delta_seconds: Absolute elapsed time between observations.
            - reason: Diagnostic text explanation.
        """
        dt_a = self.parse_timestamp(time_a)
        dt_b = self.parse_timestamp(time_b)

        delta_seconds = abs((dt_b - dt_a).total_seconds())

        if min_seconds <= delta_seconds <= max_seconds:
            # Optimal transit window: Score 0.85 to 1.0 based on center of window
            mid = (min_seconds + max_seconds) / 2.0
            span = (max_seconds - min_seconds) / 2.0 or 1.0
            deviation = abs(delta_seconds - mid) / span
            score = max(0.85, 1.0 - (0.15 * deviation))
            reason = f"Compatible transition time ({delta_seconds:.1f}s within [{min_seconds:.0f}s, {max_seconds:.0f}s] window)"
            return round(score, 3), delta_seconds, reason

        elif delta_seconds < min_seconds:
            # Too fast (unrealistic speed / teleporting)
            underflow = min_seconds - delta_seconds
            penalty = math.exp(-underflow / 3.0)  # Sharp decay
            score = 0.3 * penalty
            reason = f"Transition too fast ({delta_seconds:.1f}s < minimum {min_seconds:.0f}s)"
            return round(score, 3), delta_seconds, reason

        else:
            # Too slow (expired transition window)
            overflow = delta_seconds - max_seconds
            penalty = math.exp(-overflow / 60.0)  # Gradual decay
            score = 0.4 * penalty
            reason = f"Transition delayed/expired ({delta_seconds:.1f}s > maximum {max_seconds:.0f}s)"
            return round(score, 3), delta_seconds, reason
