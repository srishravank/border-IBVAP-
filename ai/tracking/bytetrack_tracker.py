import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timezone

from ai.tracking.basetrack import BaseTrack, TrackState
from ai.tracking.kalman_filter import KalmanFilter
from ai.tracking.matching import iou_distance, linear_assignment
from backend.models.detection import DetectionResult
from backend.models.track import TrackedObject, TrackState as TrackLifecycleState


class STrack(BaseTrack):
    """
    Individual Single Track entity for ByteTrack.
    Maintains Kalman state estimation, observed history, and trajectory points.
    """
    shared_kalman = KalmanFilter()

    def __init__(self, tlwh: np.ndarray, score: float, class_name: str, object_type: str, subclass: Optional[str] = None):
        # tlwh: [x1, y1, w, h]
        self._tlwh = np.asarray(tlwh, dtype=np.float32)
        self.kalman_filter: Optional[KalmanFilter] = None
        self.mean: Optional[np.ndarray] = None
        self.covariance: Optional[np.ndarray] = None
        self.is_activated = False

        self.score = float(score)
        self.class_name = class_name
        self.object_type = object_type
        self.subclass = subclass
        self.tracklet_len = 0
        self.trajectory: List[List[float]] = []

    def predict(self):
        mean_state = self.mean.copy()
        if self.state != TrackState.Tracked:
            mean_state[7] = 0
        self.mean, self.covariance = self.kalman_filter.predict(mean_state, self.covariance)

    def activate(self, kalman_filter: KalmanFilter, frame_id: int):
        """Start a new track."""
        self.kalman_filter = kalman_filter
        self.track_id = self.next_id()
        self.mean, self.covariance = self.kalman_filter.initiate(self.tlwh_to_xyah(self._tlwh))

        self.tracklet_len = 0
        self.state = TrackState.Tracked
        if frame_id == 1:
            self.is_activated = True
        self.frame_id = frame_id
        self.start_frame = frame_id
        
        # Add initial trajectory point
        cx, cy = self.center
        self.trajectory.append([round(cx, 1), round(cy, 1)])

    def re_activate(self, new_track: 'STrack', frame_id: int, new_id: bool = False):
        self.mean, self.covariance = self.kalman_filter.update(
            self.mean, self.covariance, self.tlwh_to_xyah(new_track.tlwh)
        )
        self.tracklet_len = 0
        self.state = TrackState.Tracked
        self.is_activated = True
        self.frame_id = frame_id
        if new_id:
            self.track_id = self.next_id()
        self.score = new_track.score
        self.class_name = new_track.class_name
        self.object_type = new_track.object_type
        self.subclass = new_track.subclass

        cx, cy = self.center
        self.trajectory.append([round(cx, 1), round(cy, 1)])

    def update(self, new_track: 'STrack', frame_id: int):
        """Update a matched track with new measurement."""
        self.frame_id = frame_id
        self.tracklet_len += 1

        new_tlwh = new_track.tlwh
        self.mean, self.covariance = self.kalman_filter.update(
            self.mean, self.covariance, self.tlwh_to_xyah(new_tlwh)
        )
        self.state = TrackState.Tracked
        self.is_activated = True

        self.score = new_track.score
        self.class_name = new_track.class_name
        self.object_type = new_track.object_type
        self.subclass = new_track.subclass

        cx, cy = self.center
        self.trajectory.append([round(cx, 1), round(cy, 1)])

    @property
    def tlwh(self) -> np.ndarray:
        """Get current position in bounding box format `(top left x, top left y, width, height)`."""
        if self.mean is None:
            return self._tlwh.copy()
        ret = self.mean[:4].copy()
        ret[2] *= ret[3]
        ret[:2] -= ret[2:] / 2
        return ret

    @property
    def tlbr(self) -> np.ndarray:
        """Convert bounding box to format `(min x, min y, max x, max y)`."""
        ret = self.tlwh.copy()
        ret[2:] += ret[:2]
        return ret

    @property
    def center(self) -> Tuple[float, float]:
        tlbr = self.tlbr
        return float((tlbr[0] + tlbr[2]) / 2.0), float((tlbr[1] + tlbr[3]) / 2.0)

    @staticmethod
    def tlwh_to_xyah(tlwh: np.ndarray) -> np.ndarray:
        """Convert bounding box to format `(center x, center y, aspect ratio, height)`."""
        ret = np.asarray(tlwh).copy()
        ret[:2] += ret[2:] / 2
        ret[2] /= ret[3]
        return ret

    @staticmethod
    def tlbr_to_tlwh(tlbr: np.ndarray) -> np.ndarray:
        ret = np.asarray(tlbr).copy()
        ret[2:] -= ret[:2]
        return ret


class ByteTrackTracker:
    """
    Multi-Object Tracker based on ByteTrack.
    Associates high- and low-score detection boxes with track predictions for persistent identification.
    """

    def __init__(
        self,
        camera_id: str,
        track_thresh: float = 0.40,
        match_thresh: float = 0.80,
        track_buffer: int = 30,
        frame_rate: int = 25,
        trajectory_history_length: int = 30
    ):
        self.camera_id = camera_id
        self.track_thresh = track_thresh
        self.match_thresh = match_thresh
        self.track_buffer = track_buffer
        self.frame_rate = frame_rate
        self.max_time_lost = int(frame_rate / 30.0 * track_buffer)
        self.trajectory_history_length = trajectory_history_length

        self.kalman_filter = KalmanFilter()
        self.tracked_stracks: List[STrack] = []
        self.lost_stracks: List[STrack] = []
        self.removed_stracks: List[STrack] = []

        self.frame_id = 0

    def reset(self):
        """Resets tracker state."""
        self.tracked_stracks.clear()
        self.lost_stracks.clear()
        self.removed_stracks.clear()
        self.frame_id = 0

    def update(self, detections: List[DetectionResult], frame_id: Optional[int] = None) -> List[TrackedObject]:
        """
        Updates the tracker with a new list of detections for the current frame.
        Returns active tracked objects with persistent IDs and trajectory history.
        """
        self.frame_id = (self.frame_id + 1) if frame_id is None else frame_id
        activated_stracks: List[STrack] = []
        refind_stracks: List[STrack] = []
        lost_stracks: List[STrack] = []
        removed_stracks: List[STrack] = []

        # 1. Split detections into high score and low score detections
        dets_high: List[STrack] = []
        dets_low: List[STrack] = []

        for det in detections:
            tlwh = STrack.tlbr_to_tlwh(np.array(det.bbox, dtype=np.float32))
            strack = STrack(
                tlwh=tlwh,
                score=det.confidence,
                class_name=det.class_name,
                object_type=det.object_type,
                subclass=det.subclass
            )
            if det.confidence >= self.track_thresh:
                dets_high.append(strack)
            else:
                dets_low.append(strack)

        # 2. Separate tracked into confirmed and unconfirmed
        unconfirmed: List[STrack] = []
        tracked_stracks: List[STrack] = []
        for track in self.tracked_stracks:
            if not track.is_activated:
                unconfirmed.append(track)
            else:
                tracked_stracks.append(track)

        # 3. Predict the current locations with Kalman Filter
        strack_pool = joint_stracks(tracked_stracks, self.lost_stracks)
        for strack in strack_pool:
            strack.predict()

        # 4. First association with high score detections
        dists = iou_distance(strack_pool, dets_high)
        matches, u_track, u_detection = linear_assignment(dists, thresh=self.match_thresh)

        for itracked, idet in matches:
            track = strack_pool[itracked]
            det = dets_high[idet]
            if track.state == TrackState.Tracked:
                track.update(det, self.frame_id)
                activated_stracks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)

        # 5. Second association with low score detections for unmatched tracks
        r_tracked_stracks = [strack_pool[i] for i in u_track if strack_pool[i].state == TrackState.Tracked]
        dists = iou_distance(r_tracked_stracks, dets_low)
        matches, u_track_second, _ = linear_assignment(dists, thresh=0.5)

        for itracked, idet in matches:
            track = r_tracked_stracks[itracked]
            det = dets_low[idet]
            if track.state == TrackState.Tracked:
                track.update(det, self.frame_id)
                activated_stracks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)

        for it in u_track_second:
            track = r_tracked_stracks[it]
            if track.state != TrackState.Lost:
                track.mark_lost()
                lost_stracks.append(track)

        # 6. Deal with unconfirmed tracks (usually tracks with only 1 frame)
        dets_high_unmatched = [dets_high[i] for i in u_detection]
        dists = iou_distance(unconfirmed, dets_high_unmatched)
        matches, u_unconfirmed, u_detection_unmatched = linear_assignment(dists, thresh=0.7)

        for itracked, idet in matches:
            unconfirmed[itracked].update(dets_high_unmatched[idet], self.frame_id)
            activated_stracks.append(unconfirmed[itracked])

        for it in u_unconfirmed:
            track = unconfirmed[it]
            track.mark_removed()
            removed_stracks.append(track)

        # 7. Initialize new tracks from remaining high-confidence detections
        for inew in u_detection_unmatched:
            track = dets_high_unmatched[inew]
            if track.score >= self.track_thresh:
                track.activate(self.kalman_filter, self.frame_id)
                activated_stracks.append(track)

        # 8. Update lost and removed tracks
        for track in self.lost_stracks:
            if self.frame_id - track.frame_id > self.max_time_lost:
                track.mark_removed()
                removed_stracks.append(track)

        # 9. Update active tracking lists
        self.tracked_stracks = [t for t in self.tracked_stracks if t.state == TrackState.Tracked]
        self.tracked_stracks = joint_stracks(self.tracked_stracks, activated_stracks)
        self.tracked_stracks = joint_stracks(self.tracked_stracks, refind_stracks)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.tracked_stracks)
        self.lost_stracks.extend(lost_stracks)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.removed_stracks)
        self.removed_stracks.extend(removed_stracks)
        self.tracked_stracks, self.lost_stracks = remove_duplicate_stracks(self.tracked_stracks, self.lost_stracks)

        # 10. Format and return active tracked objects
        output_tracks: List[TrackedObject] = []
        now_ts = datetime.now(timezone.utc).isoformat()

        for track in self.tracked_stracks:
            if not track.is_activated:
                continue

            # Trim trajectory to configured length
            if len(track.trajectory) > self.trajectory_history_length:
                track.trajectory = track.trajectory[-self.trajectory_history_length:]

            tlbr = track.tlbr
            cx, cy = track.center
            formatted_id = TrackedObject.format_track_id(track.object_type, track.track_id)

            output_tracks.append(
                TrackedObject(
                    track_id=track.track_id,
                    formatted_id=formatted_id,
                    camera_id=self.camera_id,
                    object_type=track.object_type,
                    class_name=track.class_name,
                    subclass=track.subclass,
                    confidence=round(track.score, 3),
                    bbox=[round(float(tlbr[0]), 1), round(float(tlbr[1]), 1), round(float(tlbr[2]), 1), round(float(tlbr[3]), 1)],
                    center=[round(cx, 1), round(cy, 1)],
                    trajectory=list(track.trajectory),
                    state=TrackLifecycleState.ACTIVE,
                    age=track.tracklet_len + 1,
                    time_since_update=self.frame_id - track.frame_id,
                    last_seen=now_ts,
                    frame_id=self.frame_id
                )
            )

        return output_tracks


def joint_stracks(tlist_a: List[STrack], tlist_b: List[STrack]) -> List[STrack]:
    exists = {}
    res = []
    for t in tlist_a:
        exists[t.track_id] = 1
        res.append(t)
    for t in tlist_b:
        tid = t.track_id
        if not exists.get(tid, 0):
            exists[tid] = 1
            res.append(t)
    return res


def sub_stracks(tlist_a: List[STrack], tlist_b: List[STrack]) -> List[STrack]:
    stracks = {t.track_id: t for t in tlist_a}
    for t in tlist_b:
        tid = t.track_id
        if tid in stracks:
            del stracks[tid]
    return list(stracks.values())


def remove_duplicate_stracks(stracksa: List[STrack], stracksb: List[STrack]) -> Tuple[List[STrack], List[STrack]]:
    pdist = iou_distance(stracksa, stracksb)
    pairs = np.where(pdist < 0.15)
    dupa, dupb = [], []
    for p, q in zip(*pairs):
        timep = stracksa[p].frame_id - stracksa[p].start_frame
        timeq = stracksb[q].frame_id - stracksb[q].start_frame
        if timep > timeq:
            dupb.append(q)
        else:
            dupa.append(p)
    resa = [t for i, t in enumerate(stracksa) if i not in dupa]
    resb = [t for i, t in enumerate(stracksb) if i not in dupb]
    return resa, resb
