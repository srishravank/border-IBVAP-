from enum import Enum
from typing import List, Tuple, Optional
import numpy as np


class TrackState(int, Enum):
    New = 0
    Tracked = 1
    Lost = 2
    Removed = 3


class BaseTrack:
    """Base class for tracks maintaining unique ID counters."""
    _count = 0

    track_id = 0
    is_activated = False
    state = TrackState.New

    history = []
    features = []
    curr_feature = None
    score = 0
    start_frame = 0
    frame_id = 0
    time_since_update = 0

    # Multi-camera identification
    location = (np.inf, np.inf)

    @property
    def end_frame(self):
        return self.frame_id

    @classmethod
    def next_id(cls) -> int:
        cls._count += 1
        return cls._count

    @classmethod
    def reset_counter(cls):
        cls._count = 0

    def activate(self, *args):
        raise NotImplementedError

    def predict(self):
        raise NotImplementedError

    def update(self, *args, **kwargs):
        raise NotImplementedError

    def mark_lost(self):
        self.state = TrackState.Lost

    def mark_removed(self):
        self.state = TrackState.Removed
