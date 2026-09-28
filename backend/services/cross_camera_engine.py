import time
import logging
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timezone, timedelta
import numpy as np

from backend.config import settings
from backend.database.connection import SessionLocal
from backend.database.models import (
    SubjectModel,
    SubjectTrackLinkModel,
    IncidentModel,
    IncidentEventLinkModel,
    SecurityEventModel,
    AssociatedVehicleModel,
    CameraModel
)
from backend.models.subject import (
    SubjectResponse,
    SubjectTrackLinkResponse,
    SubjectJourneyResponse,
    SubjectJourneyStep,
    IncidentResponse,
    IncidentTimelineEntry,
    MatchCandidateResponse
)
from backend.models.security_event import SecurityEventResponse
from ai.schemas.observation import AIObservation
from intelligence.matching.cross_camera_scorer import CrossCameraScorer, MatchScoreBreakdown
from intelligence.topology.camera_topology import CameraTopologyGraph
from backend.services.topology_service import topology_service
from backend.services.incident_graph import IncidentGraphBuilder
from backend.services.risk_service import risk_service

logger = logging.getLogger("ibvap.cross_camera")


class CrossCameraEngine:
    """
    Core Cross-Camera Intelligence Engine for IBVAP 2.0 (Phase 4).
    Reconstructs global subject journeys, connects multi-camera tracks,
    associates Phase 3 security events, correlates person-vehicle activity,
    and exposes the unified Incident Graph.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.scorer = CrossCameraScorer()
        
        # In-memory recent track buffer: (camera_id, track_id) -> track_dict
        self.recent_tracks: Dict[Tuple[str, int], Dict[str, Any]] = {}
        
        # Track ID to Subject ID mapping: (camera_id, track_id) -> subject_id
        self.track_to_subject: Dict[Tuple[str, int], str] = {}
        
        # Recent candidates evaluated
        self.recent_candidates: List[MatchCandidateResponse] = []
        
        self.subject_counter: int = 0
        self.vehicle_counter: int = 0
        self.incident_counter: int = 0
        self.is_initialized: bool = False

    def initialize(self):
        """Initializes database state and loads topology into memory."""
        if self.is_initialized:
            return

        topology_service.load_topology_from_db()

        db = SessionLocal()
        try:
            p_count = db.query(SubjectModel).filter(SubjectModel.object_type == "person").count()
            v_count = db.query(SubjectModel).filter(SubjectModel.object_type == "vehicle").count()
            i_count = db.query(IncidentModel).count()
            
            self.subject_counter = p_count
            self.vehicle_counter = v_count
            self.incident_counter = i_count

            # Load active mappings
            links = db.query(SubjectTrackLinkModel).all()
            for l in links:
                self.track_to_subject[(l.camera_id, l.track_id)] = l.subject_id

        finally:
            db.close()

        self.is_initialized = True
        logger.info(f"Cross-Camera Engine initialized. (Subjects: {self.subject_counter}, Vehicles: {self.vehicle_counter}, Incidents: {self.incident_counter})")

    def process_observation(self, obs: AIObservation):
        """
        Consumes live Edge AI Observations from Phase 2.
        Buffers track metadata and evaluates cross-camera candidate matching.
        """
        with self._lock:
            cam_id = obs.camera_id
            track_id = obs.object.track_id
            obj_type = obs.object.type
            center = obs.object.center
            bbox = obs.object.bbox
            traj = obs.trajectory
            ts_str = obs.timestamp
            app_vec = obs.metadata.get("appearance_vector") if obs.metadata else None

            track_key = (cam_id, track_id)
            now_dt = datetime.now(timezone.utc)

            # Update or create buffer entry
            if track_key not in self.recent_tracks:
                self.recent_tracks[track_key] = {
                    "camera_id": cam_id,
                    "track_id": track_id,
                    "formatted_id": obs.object.formatted_id,
                    "object_type": obj_type,
                    "class_name": obs.object.class_name,
                    "bbox": bbox,
                    "center": center,
                    "trajectory": traj,
                    "appearance_vector": app_vec,
                    "first_seen": ts_str,
                    "last_seen": ts_str,
                    "first_dt": now_dt,
                    "last_dt": now_dt,
                    "updates": 1
                }
                # Check for cross-camera link for new track
                self._match_new_track(track_key, self.recent_tracks[track_key])
            else:
                entry = self.recent_tracks[track_key]
                entry["center"] = center
                entry["bbox"] = bbox
                entry["trajectory"] = traj
                entry["last_seen"] = ts_str
                entry["last_dt"] = now_dt
                entry["updates"] += 1
                if app_vec is not None:
                    entry["appearance_vector"] = app_vec

            # Evaluate contextual Person-Vehicle association on same camera
            self._check_person_vehicle_association(cam_id, track_id, obj_type, center, ts_str)

            # Cleanup expired buffer entries older than SUBJECT_HISTORY_MINUTES
            self._cleanup_buffer(now_dt)

    def process_confirmed_event(self, event: SecurityEventResponse):
        """
        Consumes verified security incidents from Phase 3.
        Associates event with the global subject and connected incident.
        """
        with self._lock:
            cam_id = event.camera_id
            track_id = event.track_id
            track_key = (cam_id, track_id)

            subject_id = self.track_to_subject.get(track_key)
            if not subject_id:
                # Assign new subject for this track if not yet matched
                subject_id = self._create_new_subject(cam_id, track_id, event.object_type, event.created_at)

            # Attach event to subject's unified Incident
            self._attach_event_to_incident(subject_id, event)

    def _match_new_track(self, target_key: Tuple[str, int], target_obs: Dict[str, Any]):
        """
        Matches a newly detected track against recent tracks on connected topology cameras.
        """
        target_cam, target_tid = target_key
        target_type = target_obs["object_type"]
        topo = topology_service.graph

        # Get ancestor/neighbor cameras that connect to target_cam
        candidate_cams = topo.get_candidate_ancestors(target_cam)
        if not candidate_cams:
            candidate_cams = [c for c in ["CAM-01", "CAM-02", "CAM-03", "CAM-04"] if c != target_cam]

        best_match_score = 0.0
        best_candidate_key = None
        best_breakdown: Optional[MatchScoreBreakdown] = None

        for (src_cam, src_tid), src_obs in self.recent_tracks.items():
            if src_cam == target_cam:
                continue
            if src_obs["object_type"] != target_type:
                continue
            if src_cam not in candidate_cams:
                continue

            breakdown = self.scorer.evaluate_match(src_obs, target_obs, topo)

            # Save diagnostic candidate evaluation
            candidate_resp = MatchCandidateResponse(
                source_camera=src_cam,
                source_track_id=src_tid,
                target_camera=target_cam,
                target_track_id=target_tid,
                object_type=target_type,
                match_score=breakdown.match_score,
                match_status=breakdown.match_status,
                time_delta_seconds=breakdown.time_delta_seconds,
                evidence=breakdown.factors,
                proposed_subject_id=self.track_to_subject.get((src_cam, src_tid))
            )
            self.recent_candidates.insert(0, candidate_resp)
            self.recent_candidates = self.recent_candidates[:50]

            if breakdown.match_score > best_match_score:
                best_match_score = breakdown.match_score
                best_candidate_key = (src_cam, src_tid)
                best_breakdown = breakdown

        # If score exceeds threshold, link track to existing subject
        if best_match_score >= settings.CROSS_CAMERA_MATCH_THRESHOLD and best_candidate_key and best_breakdown:
            existing_subject_id = self.track_to_subject.get(best_candidate_key)
            if existing_subject_id:
                self._link_track_to_subject(
                    existing_subject_id,
                    target_cam,
                    target_tid,
                    target_obs["formatted_id"],
                    best_breakdown.match_score,
                    best_breakdown.match_status,
                    best_breakdown.factors,
                    target_obs["first_seen"]
                )
                logger.info(f"Cross-Camera Match Confirmed: {target_cam}/Track {target_tid} linked to {existing_subject_id} (Score: {best_match_score:.2f})")
                return

        # Otherwise create a new global subject for this entity
        self._create_new_subject(target_cam, target_tid, target_type, target_obs["first_seen"])

    def _create_new_subject(self, camera_id: str, track_id: int, object_type: str, timestamp_str: str) -> str:
        """Creates a new global subject (e.g. SUBJ-001 or VEH-001) in database."""
        db = SessionLocal()
        try:
            while True:
                if object_type == "vehicle":
                    self.vehicle_counter += 1
                    subj_id = f"VEH-{self.vehicle_counter:03d}"
                else:
                    self.subject_counter += 1
                    subj_id = f"SUBJ-{self.subject_counter:03d}"
                
                inc_id = f"INC-{subj_id}"
                existing_s = db.query(SubjectModel).filter(SubjectModel.subject_id == subj_id).first()
                existing_i = db.query(IncidentModel).filter(IncidentModel.incident_id == inc_id).first()
                if not existing_s and not existing_i:
                    break

            now_dt = datetime.now(timezone.utc)
            subj = SubjectModel(
                subject_id=subj_id,
                object_type=object_type,
                status="ACTIVE",
                first_seen=now_dt,
                last_seen=now_dt,
                initial_camera_id=camera_id,
                initial_track_id=track_id,
                total_cameras_visited=1,
                created_at=now_dt
            )
            db.add(subj)

            # Create initial link
            link = SubjectTrackLinkModel(
                subject_id=subj_id,
                camera_id=camera_id,
                track_id=track_id,
                formatted_track_id=f"{'V' if object_type == 'vehicle' else 'P'}{track_id:03d}",
                match_score=1.0,
                match_status="CONFIRMED_LINK",
                evidence_json='["Initial detection origin on border sensor"]',
                first_timestamp=now_dt,
                last_timestamp=now_dt,
                linked_at=now_dt
            )
            db.add(link)

            # Create parent Incident
            self.incident_counter += 1
            inc = IncidentModel(
                incident_id=inc_id,
                subject_id=subj_id,
                status="ACTIVE",
                title=f"Multi-Sensor Tracking for {subj_id} ({object_type.upper()})",
                summary=f"Unified incident tracking journey across camera sensors starting on {camera_id}.",
                created_at=now_dt,
                updated_at=now_dt
            )
            db.add(inc)

            db.commit()

            self.track_to_subject[(camera_id, track_id)] = subj_id
        finally:
            db.close()

        # Phase 5: Initial Risk Assessment (evaluated after DB session is closed)
        risk_service.evaluate_incident(inc_id)
        return subj_id

    def _link_track_to_subject(
        self,
        subject_id: str,
        camera_id: str,
        track_id: int,
        formatted_id: str,
        match_score: float,
        match_status: str,
        factors: List[str],
        timestamp_str: str
    ):
        """Links an observed camera track to an existing subject."""
        db = SessionLocal()
        inc_id = None
        try:
            now_dt = datetime.now(timezone.utc)
            link = SubjectTrackLinkModel(
                subject_id=subject_id,
                camera_id=camera_id,
                track_id=track_id,
                formatted_track_id=formatted_id,
                match_score=match_score,
                match_status=match_status,
                evidence=factors,
                first_timestamp=now_dt,
                last_timestamp=now_dt,
                linked_at=now_dt
            )
            db.add(link)

            # Update Subject last_seen and visited camera count
            subj = db.query(SubjectModel).filter(SubjectModel.subject_id == subject_id).first()
            if subj:
                subj.last_seen = now_dt
                visited_cams = db.query(SubjectTrackLinkModel.camera_id).filter(
                    SubjectTrackLinkModel.subject_id == subject_id
                ).distinct().count()
                subj.total_cameras_visited = max(subj.total_cameras_visited, visited_cams + 1)

            # Update Incident updated_at
            inc = db.query(IncidentModel).filter(IncidentModel.subject_id == subject_id).first()
            if inc:
                inc_id = inc.incident_id
                inc.updated_at = now_dt

            db.commit()
            self.track_to_subject[(camera_id, track_id)] = subject_id
        finally:
            db.close()

        # Phase 5: Re-evaluate Risk on track link (evaluated after DB session is closed)
        if inc_id:
            risk_service.evaluate_incident(inc_id)

    def _attach_event_to_incident(self, subject_id: str, event: SecurityEventResponse):
        """Maps a confirmed Phase 3 event to the Subject's Incident in sequence."""
        db = SessionLocal()
        inc_id = None
        try:
            inc = db.query(IncidentModel).filter(IncidentModel.subject_id == subject_id).first()
            if not inc:
                return

            inc_id = inc.incident_id
            # Check if already linked
            existing_link = db.query(IncidentEventLinkModel).filter(
                IncidentEventLinkModel.incident_id == inc.incident_id,
                IncidentEventLinkModel.event_id == event.event_id
            ).first()
            if existing_link:
                return

            seq_num = db.query(IncidentEventLinkModel).filter(
                IncidentEventLinkModel.incident_id == inc.incident_id
            ).count() + 1

            link = IncidentEventLinkModel(
                incident_id=inc.incident_id,
                event_id=event.event_id,
                sequence_number=seq_num,
                linked_at=datetime.now(timezone.utc)
            )
            db.add(link)
            inc.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"Attached event '{event.event_id}' (Seq: #{seq_num}) to Incident '{inc.incident_id}' for Subject '{subject_id}'")
        finally:
            db.close()

        # Phase 5: Re-evaluate Risk on verified security event attachment (after DB session closed)
        if inc_id:
            risk_service.evaluate_incident(inc_id, force=True)

    def _check_person_vehicle_association(self, camera_id: str, track_id: int, obj_type: str, center: List[float], ts_str: str):
        """
        Evaluates contextual proximity between nearby person and vehicle tracks on the same camera.
        Strictly applies neutral terminology ("related activity", "spatially/temporally associated").
        """
        if not center or len(center) < 2:
            return

        cx, cy = center[0], center[1]
        now_dt = datetime.now(timezone.utc)

        # Look for complementary object types on same camera
        target_type = "vehicle" if obj_type == "person" else "person"

        for (cam, tid), obs in self.recent_tracks.items():
            if cam != camera_id or tid == track_id or obs["object_type"] != target_type:
                continue

            other_center = obs.get("center")
            if not other_center or len(other_center) < 2:
                continue

            dist_px = float(np.hypot(cx - other_center[0], cy - other_center[1]))
            if dist_px <= settings.VEHICLE_PROXIMITY_MAX_DISTANCE_PX:
                # Estimate distance in meters (approx 30px ~ 1 meter)
                dist_m = round(dist_px / 30.0, 1)

                person_tid = track_id if obj_type == "person" else tid
                vehicle_tid = tid if obj_type == "person" else track_id

                person_subj_id = self.track_to_subject.get((camera_id, person_tid))
                veh_subj_id = self.track_to_subject.get((camera_id, vehicle_tid))

                if person_subj_id and veh_subj_id and person_subj_id != veh_subj_id:
                    self._record_vehicle_association(
                        person_subj_id, veh_subj_id, camera_id, person_tid, vehicle_tid, dist_m, now_dt
                    )

    def _record_vehicle_association(
        self,
        subject_id: str,
        vehicle_subject_id: str,
        camera_id: str,
        person_tid: int,
        vehicle_tid: int,
        dist_m: float,
        timestamp: datetime
    ):
        db = SessionLocal()
        inc_id = None
        try:
            # Check duplicate
            existing = db.query(AssociatedVehicleModel).filter(
                AssociatedVehicleModel.subject_id == subject_id,
                AssociatedVehicleModel.vehicle_subject_id == vehicle_subject_id
            ).first()
            if existing:
                return

            assoc = AssociatedVehicleModel(
                subject_id=subject_id,
                vehicle_subject_id=vehicle_subject_id,
                camera_id=camera_id,
                person_track_id=person_tid,
                vehicle_track_id=vehicle_tid,
                relationship_type="ASSOCIATED_WITH",
                proximity_meters=dist_m,
                time_delta_seconds=0.0,
                timestamp=timestamp,
                notes=f"Spatially and temporally associated activity near {camera_id} (~{dist_m:.0f}m proximity)"
            )
            db.add(assoc)

            inc = db.query(IncidentModel).filter(IncidentModel.subject_id == subject_id).first()
            if inc:
                inc_id = inc.incident_id

            db.commit()
            logger.info(f"Recorded contextual association: Subject '{subject_id}' <-> Vehicle '{vehicle_subject_id}' on {camera_id}")
        finally:
            db.close()

        # Phase 5: Re-evaluate Risk on vehicle association (after DB session closed)
        if inc_id:
            risk_service.evaluate_incident(inc_id, force=True)

    def _cleanup_buffer(self, now_dt: datetime):
        cutoff = now_dt - timedelta(minutes=settings.SUBJECT_HISTORY_MINUTES)
        expired_keys = [k for k, v in self.recent_tracks.items() if v.get("last_dt", now_dt) < cutoff]
        for k in expired_keys:
            del self.recent_tracks[k]

    # --- Query Methods for API and Downstream (Phase 5 Interface) ---

    def get_all_subjects(self) -> List[SubjectResponse]:
        db = SessionLocal()
        try:
            subjs = db.query(SubjectModel).order_by(SubjectModel.last_seen.desc()).all()
            res = []
            for s in subjs:
                links = db.query(SubjectTrackLinkModel).filter(
                    SubjectTrackLinkModel.subject_id == s.subject_id
                ).all()
                res.append(SubjectResponse(
                    subject_id=s.subject_id,
                    object_type=s.object_type,
                    status=s.status,
                    first_seen=s.first_seen.isoformat(),
                    last_seen=s.last_seen.isoformat(),
                    initial_camera_id=s.initial_camera_id,
                    initial_track_id=s.initial_track_id,
                    total_cameras_visited=s.total_cameras_visited,
                    created_at=s.created_at.isoformat(),
                    track_links=[
                        SubjectTrackLinkResponse(
                            id=l.id,
                            subject_id=l.subject_id,
                            camera_id=l.camera_id,
                            track_id=l.track_id,
                            formatted_track_id=l.formatted_track_id,
                            match_score=l.match_score,
                            match_status=l.match_status,
                            evidence=l.evidence,
                            first_timestamp=l.first_timestamp.isoformat(),
                            last_timestamp=l.last_timestamp.isoformat(),
                            linked_at=l.linked_at.isoformat()
                        )
                        for l in links
                    ]
                ))
            return res
        finally:
            db.close()

    def get_subject_by_id(self, subject_id: str) -> Optional[SubjectResponse]:
        db = SessionLocal()
        try:
            s = db.query(SubjectModel).filter(SubjectModel.subject_id == subject_id).first()
            if not s:
                return None
            links = db.query(SubjectTrackLinkModel).filter(
                SubjectTrackLinkModel.subject_id == s.subject_id
            ).order_by(SubjectTrackLinkModel.first_timestamp.asc()).all()

            return SubjectResponse(
                subject_id=s.subject_id,
                object_type=s.object_type,
                status=s.status,
                first_seen=s.first_seen.isoformat(),
                last_seen=s.last_seen.isoformat(),
                initial_camera_id=s.initial_camera_id,
                initial_track_id=s.initial_track_id,
                total_cameras_visited=s.total_cameras_visited,
                created_at=s.created_at.isoformat(),
                track_links=[
                    SubjectTrackLinkResponse(
                        id=l.id,
                        subject_id=l.subject_id,
                        camera_id=l.camera_id,
                        track_id=l.track_id,
                        formatted_track_id=l.formatted_track_id,
                        match_score=l.match_score,
                        match_status=l.match_status,
                        evidence=l.evidence,
                        first_timestamp=l.first_timestamp.isoformat(),
                        last_timestamp=l.last_timestamp.isoformat(),
                        linked_at=l.linked_at.isoformat()
                    )
                    for l in links
                ]
            )
        finally:
            db.close()

    def get_subject_journey(self, subject_id: str) -> Optional[SubjectJourneyResponse]:
        db = SessionLocal()
        try:
            s = db.query(SubjectModel).filter(SubjectModel.subject_id == subject_id).first()
            if not s:
                return None

            links = db.query(SubjectTrackLinkModel).filter(
                SubjectTrackLinkModel.subject_id == subject_id
            ).order_by(SubjectTrackLinkModel.first_timestamp.asc()).all()

            cams_map = {c.camera_id: c.camera_name for c in db.query(CameraModel).all()}

            steps: List[SubjectJourneyStep] = []
            cams_seq: List[str] = []

            for idx, l in enumerate(links):
                cams_seq.append(l.camera_id)

                # Get events triggered by this track on this camera
                events = db.query(SecurityEventModel).filter(
                    SecurityEventModel.camera_id == l.camera_id,
                    SecurityEventModel.track_id == l.track_id
                ).all()

                # Get associated vehicles on this camera
                vehicles = db.query(AssociatedVehicleModel).filter(
                    AssociatedVehicleModel.subject_id == subject_id,
                    AssociatedVehicleModel.camera_id == l.camera_id
                ).all()

                steps.append(SubjectJourneyStep(
                    sequence=idx + 1,
                    camera_id=l.camera_id,
                    camera_name=cams_map.get(l.camera_id, f"Camera {l.camera_id}"),
                    track_id=l.track_id,
                    formatted_track_id=l.formatted_track_id,
                    first_seen=l.first_timestamp.isoformat(),
                    last_seen=l.last_timestamp.isoformat(),
                    match_score=l.match_score,
                    match_status=l.match_status,
                    evidence=l.evidence,
                    events_triggered=[
                        {
                            "event_id": e.event_id,
                            "event_type": e.event_type,
                            "zone_name": e.zone_name,
                            "status": e.status,
                            "confidence": e.confidence,
                            "timestamp": e.created_at.isoformat()
                        }
                        for e in events
                    ],
                    associated_vehicles=[
                        {
                            "vehicle_id": v.vehicle_subject_id,
                            "proximity_meters": v.proximity_meters,
                            "timestamp": v.timestamp.isoformat(),
                            "notes": v.notes
                        }
                        for v in vehicles
                    ]
                ))

            return SubjectJourneyResponse(
                subject_id=s.subject_id,
                object_type=s.object_type,
                first_seen=s.first_seen.isoformat(),
                last_seen=s.last_seen.isoformat(),
                total_cameras=len(set(cams_seq)),
                cameras_sequence=cams_seq,
                journey_steps=steps
            )
        finally:
            db.close()

    def get_incidents(self) -> List[IncidentResponse]:
        db = SessionLocal()
        try:
            incidents = db.query(IncidentModel).order_by(IncidentModel.updated_at.desc()).all()
            res = []
            for inc in incidents:
                links = db.query(SubjectTrackLinkModel).filter(
                    SubjectTrackLinkModel.subject_id == inc.subject_id
                ).all()
                cams = list(set([l.camera_id for l in links]))

                event_count = db.query(IncidentEventLinkModel).filter(
                    IncidentEventLinkModel.incident_id == inc.incident_id
                ).count()

                veh_count = db.query(AssociatedVehicleModel).filter(
                    AssociatedVehicleModel.subject_id == inc.subject_id
                ).count()

                res.append(IncidentResponse(
                    incident_id=inc.incident_id,
                    subject_id=inc.subject_id,
                    status=inc.status,
                    title=inc.title,
                    summary=inc.summary,
                    created_at=inc.created_at.isoformat(),
                    updated_at=inc.updated_at.isoformat(),
                    cameras_involved=cams,
                    events_count=event_count,
                    associated_vehicles_count=veh_count
                ))
            return res
        finally:
            db.close()

    def get_incident_timeline(self, incident_id: str) -> List[IncidentTimelineEntry]:
        db = SessionLocal()
        try:
            inc = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
            if not inc:
                return []

            subject_id = inc.subject_id
            cams_map = {c.camera_id: c.camera_name for c in db.query(CameraModel).all()}

            timeline: List[IncidentTimelineEntry] = []

            # 1. Subject track links across cameras
            links = db.query(SubjectTrackLinkModel).filter(
                SubjectTrackLinkModel.subject_id == subject_id
            ).all()

            for l in links:
                timeline.append(IncidentTimelineEntry(
                    timestamp=l.first_timestamp.isoformat(),
                    camera_id=l.camera_id,
                    camera_name=cams_map.get(l.camera_id, l.camera_id),
                    entry_type="OBSERVATION",
                    title=f"Observed on {l.camera_id} (#{l.track_id})",
                    description=f"Initial tracking lock established for {subject_id} as local track {l.formatted_track_id}.",
                    track_id=l.track_id,
                    subject_id=subject_id,
                    details={"match_score": l.match_score, "evidence": l.evidence}
                ))

                if l.match_score < 1.0:
                    timeline.append(IncidentTimelineEntry(
                        timestamp=l.linked_at.isoformat(),
                        camera_id=l.camera_id,
                        camera_name=cams_map.get(l.camera_id, l.camera_id),
                        entry_type="MATCH_CONFIRMED",
                        title=f"Cross-Camera Match Confirmed ({l.camera_id})",
                        description=f"Evidence verification linked local track {l.formatted_track_id} to global subject {subject_id} (Confidence: {l.match_score * 100:.0f}%).",
                        track_id=l.track_id,
                        subject_id=subject_id,
                        details={"match_score": l.match_score, "evidence": l.evidence}
                    ))

            # 2. Confirmed Zone Events
            event_links = db.query(IncidentEventLinkModel).filter(
                IncidentEventLinkModel.incident_id == incident_id
            ).order_by(IncidentEventLinkModel.sequence_number.asc()).all()

            for el in event_links:
                evt = db.query(SecurityEventModel).filter(SecurityEventModel.event_id == el.event_id).first()
                if evt:
                    timeline.append(IncidentTimelineEntry(
                        timestamp=evt.created_at.isoformat(),
                        camera_id=evt.camera_id,
                        camera_name=cams_map.get(evt.camera_id, evt.camera_id),
                        entry_type="ZONE_EVENT",
                        title=f"{evt.event_type} Confirmed in {evt.zone_name}",
                        description=f"Multi-frame verified intrusion event on {evt.camera_id} for track #{evt.track_id}.",
                        track_id=evt.track_id,
                        subject_id=subject_id,
                        details={"event_id": evt.event_id, "confidence": evt.confidence, "zone_id": evt.zone_id}
                    ))

            # 3. Contextual Vehicles
            vehicles = db.query(AssociatedVehicleModel).filter(
                AssociatedVehicleModel.subject_id == subject_id
            ).all()

            for v in vehicles:
                timeline.append(IncidentTimelineEntry(
                    timestamp=v.timestamp.isoformat(),
                    camera_id=v.camera_id,
                    camera_name=cams_map.get(v.camera_id, v.camera_id),
                    entry_type="VEHICLE_ASSOCIATED",
                    title=f"Contextual Vehicle Associated ({v.vehicle_subject_id})",
                    description=f"{v.notes}",
                    track_id=v.person_track_id,
                    subject_id=subject_id,
                    details={"vehicle_id": v.vehicle_subject_id, "proximity_m": v.proximity_meters}
                ))

            # Sort timeline chronologically
            timeline.sort(key=lambda x: x.timestamp)
            return timeline
        finally:
            db.close()

    def get_incident_graph(self, incident_id: str):
        db = SessionLocal()
        try:
            inc = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
            if not inc:
                return None
            return IncidentGraphBuilder.build_graph_for_subject(inc.subject_id, incident_id=incident_id)
        finally:
            db.close()

    def get_matching_candidates(self) -> List[MatchCandidateResponse]:
        with self._lock:
            return list(self.recent_candidates)


# Global singleton Cross-Camera Intelligence engine
cross_camera_engine = CrossCameraEngine()
