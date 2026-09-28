from typing import Dict, Tuple, Optional, Set
from backend.models.security_event import SecurityEventType


class TrackZoneStateManager:
    """
    Manages track-zone spatial relationship state machine:
    - OUTSIDE -> INSIDE: triggers ZONE_ENTRY candidate
    - INSIDE -> OUTSIDE: triggers ZONE_EXIT candidate
    - INSIDE -> INSIDE: lingering (deduplicated; no new event generated)
    """

    def __init__(self):
        # Key: (camera_id, track_id, zone_id) -> "INSIDE" | "OUTSIDE"
        self._states: Dict[Tuple[str, int, str], str] = {}
        
        # Deduplication tracker: Set of (camera_id, track_id, zone_id, event_type)
        # Prevents generating repeated confirmed events while target remains in the same zone state
        self._confirmed_state_keys: Set[Tuple[str, int, str, str]] = set()

    def get_state(self, camera_id: str, track_id: int, zone_id: str) -> str:
        return self._states.get((camera_id, track_id, zone_id), "OUTSIDE")

    def evaluate_transition(
        self,
        camera_id: str,
        track_id: int,
        zone_id: str,
        is_currently_inside: bool
    ) -> Optional[SecurityEventType]:
        """
        Evaluates boundary crossing transition.
        Returns the appropriate event type if a state transition occurred, or None if state is unchanged.
        """
        key = (camera_id, track_id, zone_id)
        prev_state = self._states.get(key, "OUTSIDE")
        curr_state = "INSIDE" if is_currently_inside else "OUTSIDE"

        if prev_state == curr_state:
            return None  # No boundary transition

        # Update state
        self._states[key] = curr_state

        if prev_state == "OUTSIDE" and curr_state == "INSIDE":
            # Clear exit confirmed flag if present
            self._confirmed_state_keys.discard((camera_id, track_id, zone_id, SecurityEventType.ZONE_EXIT.value))
            return SecurityEventType.ZONE_ENTRY

        if prev_state == "INSIDE" and curr_state == "OUTSIDE":
            # Clear entry confirmed flag
            self._confirmed_state_keys.discard((camera_id, track_id, zone_id, SecurityEventType.ZONE_ENTRY.value))
            self._confirmed_state_keys.discard((camera_id, track_id, zone_id, SecurityEventType.ZONE_INTRUSION.value))
            return SecurityEventType.ZONE_EXIT

        return None

    def is_already_confirmed(self, camera_id: str, track_id: int, zone_id: str, event_type: str) -> bool:
        """Deduplication check: returns True if this specific transition is already confirmed."""
        return (camera_id, track_id, zone_id, event_type) in self._confirmed_state_keys

    def mark_confirmed(self, camera_id: str, track_id: int, zone_id: str, event_type: str):
        """Marks a transition as confirmed to deduplicate subsequent frames."""
        self._confirmed_state_keys.add((camera_id, track_id, zone_id, event_type))

    def cleanup_track(self, camera_id: str, track_id: int):
        """Removes state records when a track is removed or lost."""
        keys_to_del = [k for k in self._states.keys() if k[0] == camera_id and k[1] == track_id]
        for k in keys_to_del:
            del self._states[k]
        
        self._confirmed_state_keys = {
            k for k in self._confirmed_state_keys if not (k[0] == camera_id and k[1] == track_id)
        }
