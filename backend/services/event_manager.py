import time
import logging
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timezone

from backend.config import settings
from backend.database.connection import SessionLocal
from backend.database.models import SecurityEventModel
from backend.models.security_event import (
    SecurityEventType,
    EventStatus,
    VerificationDetail,
    SecurityEventResponse
)
from backend.models.event import CameraEvent, EventType
from backend.models.camera import CameraStatus
from ai.schemas.observation import AIObservation
from verification.polygon_engine import point_in_polygon, get_reference_point
from verification.false_positive_filter import CompositeFalsePositiveFilter
from verification.temporal_gate import CandidateVerificationTracker
from verification.event_state_machine import TrackZoneStateManager
from backend.services.zone_engine import zone_engine
from backend.services.camera_manager import camera_manager

logger = logging.getLogger("ibvap.verification")


class EventManager:
    """
    Core Event & Multi-Frame Verification Engine for IBVAP 2.0 (Phase 3).
    Evaluates virtual fence polygon intersections, enforces multi-frame temporal confirmation,
    suppresses false alarms, and stores verified security incidents.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.state_manager = TrackZoneStateManager()
        self.suppression_filter = CompositeFalsePositiveFilter()
        
        # Key: candidate_key -> CandidateVerificationTracker
        self.active_candidates: Dict[str, CandidateVerificationTracker] = {}
        
        # Phase 4 downstream event subscribers
        self.confirmed_event_subscribers: List[Callable[[SecurityEventResponse], None]] = []
        
        self.event_counter: int = 0
        self.is_initialized: bool = False

    def initialize(self):
        """Initializes state and pre-syncs event counter from database."""
        if self.is_initialized:
            return
        
        zone_engine.load_zones_from_db()
        db = SessionLocal()
        try:
            count = db.query(SecurityEventModel).count()
            self.event_counter = count
        except Exception:
            self.event_counter = 0
        finally:
            db.close()

        self.is_initialized = True
        logger.info(f"Event & Verification Engine initialized. Current event count: {self.event_counter}")

    def register_confirmed_event_subscriber(self, callback: Callable[[SecurityEventResponse], None]):
        """Registers a Phase 4 Cross-Camera Intelligence subscriber for confirmed security events."""
        if callback not in self.confirmed_event_subscribers:
            self.confirmed_event_subscribers.append(callback)

    def process_observation(self, obs: AIObservation):
        """
        Main ingress pipeline for Phase 2 structured AI observations.
        Evaluates virtual fences, manages candidate states, and runs verification gates.
        """
        if not settings.ZONE_ENABLED:
            return

        camera_id = obs.camera_id
        track_id = obs.object.track_id
        frame_id = obs.frame_id
        
        # 1. Fetch configured zones for this camera
        zones = zone_engine.get_zones_for_camera(camera_id, enabled_only=True)
        if not zones:
            return

        # 2. Get camera health status (for false-positive health isolation)
        cam_status = CameraStatus.ONLINE
        worker = camera_manager.workers.get(camera_id)
        if worker and worker.health_monitor:
            cam_status = worker.health_monitor.current_status

        # 3. Calculate Ground-Plane Reference Point (Bottom-Center of bbox)
        ref_x, ref_y = get_reference_point(obs.object.bbox, obs.object.type)
        ref_pt = (ref_x, ref_y)

        # 4. Check polygon intersection for all enabled zones
        with self._lock:
            for zone in zones:
                is_inside = point_in_polygon(ref_pt, zone.polygon)
                
                # Check boundary transition
                transition = self.state_manager.evaluate_transition(
                    camera_id=camera_id,
                    track_id=track_id,
                    zone_id=zone.zone_id,
                    is_currently_inside=is_inside
                )

                candidate_key = f"{camera_id}:{track_id}:{zone.zone_id}:ZONE_INTRUSION"
                
                # If newly entered or boundary crossed
                if transition == SecurityEventType.ZONE_ENTRY or (is_inside and candidate_key not in self.active_candidates and not self.state_manager.is_already_confirmed(camera_id, track_id, zone.zone_id, "ZONE_INTRUSION")):
                    # Create new candidate tracker
                    self.active_candidates[candidate_key] = CandidateVerificationTracker(
                        candidate_key=candidate_key,
                        camera_id=camera_id,
                        track_id=track_id,
                        zone_id=zone.zone_id,
                        event_type=SecurityEventType.ZONE_INTRUSION.value,
                        required_frames=settings.VERIFICATION_REQUIRED_FRAMES,
                        window_frames=settings.VERIFICATION_WINDOW_FRAMES,
                        max_age_frames=settings.MAX_CANDIDATE_AGE_FRAMES
                    )
                    logger.debug(f"[{camera_id}] Candidate event created: {candidate_key}")

                # If candidate is active, feed new observation into verification gate
                if candidate_key in self.active_candidates:
                    candidate = self.active_candidates[candidate_key]
                    
                    if is_inside:
                        # Run False-Positive Suppression Filters
                        is_valid, reasons = self.suppression_filter.evaluate(
                            observation=obs,
                            camera_status=cam_status
                        )

                        # Advance multi-frame verification gate
                        status, v_detail = candidate.add_observation(
                            obs=obs,
                            is_valid_suppression=is_valid,
                            reasons=reasons
                        )

                        # Check if promoted to CONFIRMED
                        if status == EventStatus.CONFIRMED:
                            if not self.state_manager.is_already_confirmed(camera_id, track_id, zone.zone_id, "ZONE_INTRUSION"):
                                self._promote_to_confirmed_event(candidate, obs, zone, v_detail, ref_pt)
                                self.state_manager.mark_confirmed(camera_id, track_id, zone.zone_id, "ZONE_INTRUSION")
                            del self.active_candidates[candidate_key]

                        elif status in (EventStatus.REJECTED, EventStatus.EXPIRED):
                            logger.info(f"[{camera_id}] Candidate '{candidate_key}' {status.value} (Reasons: {v_detail.suppression_reasons})")
                            del self.active_candidates[candidate_key]
                    else:
                        # Target moved outside before verification was complete
                        candidate.check_timeout(frame_id)
                        if candidate.status in (EventStatus.EXPIRED, EventStatus.REJECTED):
                            del self.active_candidates[candidate_key]

                # Check if exit event occurred
                if transition == SecurityEventType.ZONE_EXIT:
                    # Clean up candidate if still pending
                    if candidate_key in self.active_candidates:
                        del self.active_candidates[candidate_key]
                    
                    # Optionally record exit if target had confirmed intrusion
                    if self.state_manager.is_already_confirmed(camera_id, track_id, zone.zone_id, "ZONE_INTRUSION"):
                        self._record_exit_event(camera_id, track_id, obs, zone, ref_pt)

    def _promote_to_confirmed_event(
        self,
        candidate: CandidateVerificationTracker,
        obs: AIObservation,
        zone: Any,
        v_detail: VerificationDetail,
        ref_pt: Tuple[float, float]
    ):
        """Persists confirmed security incident and broadcasts alerts to WebSocket & subscribers."""
        self.event_counter += 1
        event_id = f"EVT-{self.event_counter:06d}"
        now_ts = datetime.now(timezone.utc)

        desc = f"Verified {obs.object.type} intrusion in restricted zone '{zone.zone_name}' (Target: {obs.object.formatted_id}, Confidence: {obs.object.confidence:.2f})"
        
        # 1. Save to Database
        db = SessionLocal()
        try:
            model = SecurityEventModel(
                event_id=event_id,
                camera_id=candidate.camera_id,
                track_id=candidate.track_id,
                formatted_track_id=obs.object.formatted_id,
                zone_id=zone.zone_id,
                zone_name=zone.zone_name,
                event_type=SecurityEventType.ZONE_INTRUSION.value,
                status=EventStatus.CONFIRMED.value,
                confidence=round(v_detail.average_confidence or obs.object.confidence, 3),
                object_type=obs.object.type,
                class_name=obs.object.class_name,
                subclass=obs.object.subclass,
                bbox_json=str(obs.object.bbox),
                reference_point_json=str([round(ref_pt[0], 1), round(ref_pt[1], 1)]),
                trajectory_json=str(obs.trajectory),
                verification_json=str(v_detail.model_dump()),
                description=desc,
                created_at=datetime.fromisoformat(candidate.created_at) if candidate.created_at else now_ts,
                confirmed_at=now_ts
            )
            db.add(model)
            db.commit()
            logger.warning(f"🚨 [CONFIRMED SECURITY EVENT] [{event_id}] {desc}")
        except Exception as e:
            logger.error(f"Failed to persist confirmed event to database: {e}")
            db.rollback()
        finally:
            db.close()

        # 2. Build Response Object
        event_resp = SecurityEventResponse(
            event_id=event_id,
            camera_id=candidate.camera_id,
            track_id=candidate.track_id,
            formatted_track_id=obs.object.formatted_id,
            zone_id=zone.zone_id,
            zone_name=zone.zone_name,
            event_type=SecurityEventType.ZONE_INTRUSION,
            status=EventStatus.CONFIRMED,
            created_at=candidate.created_at,
            confirmed_at=now_ts.isoformat(),
            confidence=round(v_detail.average_confidence or obs.object.confidence, 3),
            object_type=obs.object.type,
            class_name=obs.object.class_name,
            subclass=obs.object.subclass,
            bbox=obs.object.bbox,
            reference_point=[round(ref_pt[0], 1), round(ref_pt[1], 1)],
            trajectory=obs.trajectory,
            verification=v_detail,
            description=desc
        )

        # 3. Broadcast to WebSocket / CameraManager event bus
        camera_manager._broadcast_event(
            CameraEvent(
                event_type=EventType.INTRUSION,
                camera_id=candidate.camera_id,
                frame_id=obs.frame_id,
                track_id=candidate.track_id,
                object_type=obs.object.type,
                confidence=event_resp.confidence,
                message=desc,
                details={
                    "event_id": event_id,
                    "zone_id": zone.zone_id,
                    "zone_name": zone.zone_name,
                    "verification": v_detail.model_dump()
                }
            )
        )

        # 4. Dispatch to Phase 4 Cross-Camera Intelligence subscribers
        for sub in list(self.confirmed_event_subscribers):
            try:
                sub(event_resp)
            except Exception as e:
                logger.error(f"Phase 4 subscriber error: {e}")

    def _record_exit_event(self, camera_id: str, track_id: int, obs: AIObservation, zone: Any, ref_pt: Tuple[float, float]):
        """Logs departure/exit from a restricted virtual zone."""
        self.event_counter += 1
        event_id = f"EVT-{self.event_counter:06d}"
        now_ts = datetime.now(timezone.utc)
        desc = f"{obs.object.type.capitalize()} {obs.object.formatted_id} exited restricted zone '{zone.zone_name}'"

        db = SessionLocal()
        try:
            model = SecurityEventModel(
                event_id=event_id,
                camera_id=camera_id,
                track_id=track_id,
                formatted_track_id=obs.object.formatted_id,
                zone_id=zone.zone_id,
                zone_name=zone.zone_name,
                event_type=SecurityEventType.ZONE_EXIT.value,
                status=EventStatus.CONFIRMED.value,
                confidence=obs.object.confidence,
                object_type=obs.object.type,
                class_name=obs.object.class_name,
                subclass=obs.object.subclass,
                bbox_json=str(obs.object.bbox),
                reference_point_json=str([round(ref_pt[0], 1), round(ref_pt[1], 1)]),
                trajectory_json=str(obs.trajectory),
                verification_json=str({"verification_status": "PASSED"}),
                description=desc,
                created_at=now_ts,
                confirmed_at=now_ts
            )
            db.add(model)
            db.commit()
            logger.info(f"[{event_id}] {desc}")
        except Exception as e:
            db.rollback()
        finally:
            db.close()

    def get_security_events(
        self,
        camera_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[SecurityEventResponse]:
        """Queries stored security incidents with optional filters."""
        db = SessionLocal()
        try:
            query = db.query(SecurityEventModel)
            if camera_id:
                query = query.filter(SecurityEventModel.camera_id == camera_id)
            if zone_id:
                query = query.filter(SecurityEventModel.zone_id == zone_id)
            if event_type:
                query = query.filter(SecurityEventModel.event_type == event_type)
            if status:
                query = query.filter(SecurityEventModel.status == status)

            records = query.order_by(SecurityEventModel.created_at.desc()).limit(limit).all()
            return [self._model_to_response(r) for r in records]
        finally:
            db.close()

    def get_event_by_id(self, event_id: str) -> Optional[SecurityEventResponse]:
        db = SessionLocal()
        try:
            rec = db.query(SecurityEventModel).filter(SecurityEventModel.event_id == event_id).first()
            return self._model_to_response(rec) if rec else None
        finally:
            db.close()

    def acknowledge_event(self, event_id: str, notes: Optional[str] = None) -> Optional[SecurityEventResponse]:
        """Operator acknowledgment of a confirmed security incident."""
        db = SessionLocal()
        try:
            rec = db.query(SecurityEventModel).filter(SecurityEventModel.event_id == event_id).first()
            if not rec:
                return None
            rec.status = EventStatus.ACKNOWLEDGED.value
            rec.acknowledged_at = datetime.now(timezone.utc)
            if notes:
                rec.description = f"{rec.description} | Acknowledged: {notes}"
            db.commit()
            db.refresh(rec)
            return self._model_to_response(rec)
        finally:
            db.close()

    def get_active_verifying_candidates(self, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns in-progress candidate events currently undergoing multi-frame verification."""
        with self._lock:
            candidates = []
            for k, cand in self.active_candidates.items():
                if camera_id and cand.camera_id != camera_id:
                    continue
                candidates.append({
                    "candidate_key": cand.candidate_key,
                    "camera_id": cand.camera_id,
                    "track_id": cand.track_id,
                    "zone_id": cand.zone_id,
                    "event_type": cand.event_type,
                    "status": cand.status.value,
                    "confirmed_frames": len(cand.supporting_frame_ids),
                    "required_frames": cand.required_frames,
                    "progress_pct": round(len(cand.supporting_frame_ids) / cand.required_frames * 100, 1),
                    "latest_confidence": cand.latest_observation.object.confidence if cand.latest_observation else 0.0,
                    "object_type": cand.latest_observation.object.type if cand.latest_observation else "unknown",
                    "formatted_track_id": cand.latest_observation.object.formatted_id if cand.latest_observation else str(cand.track_id)
                })
            return candidates

    def _model_to_response(self, model: SecurityEventModel) -> SecurityEventResponse:
        v_dict = model.verification or {}
        v_detail = VerificationDetail(
            required_frames=v_dict.get("required_frames", 3),
            confirmed_frames=v_dict.get("confirmed_frames", 3),
            verification_status=v_dict.get("verification_status", "PASSED"),
            supporting_frame_ids=v_dict.get("supporting_frame_ids", []),
            average_confidence=v_dict.get("average_confidence", model.confidence),
            suppression_reasons=v_dict.get("suppression_reasons", [])
        )

        return SecurityEventResponse(
            event_id=model.event_id,
            camera_id=model.camera_id,
            track_id=model.track_id,
            formatted_track_id=model.formatted_track_id,
            zone_id=model.zone_id,
            zone_name=model.zone_name,
            event_type=SecurityEventType(model.event_type),
            status=EventStatus(model.status),
            created_at=model.created_at.isoformat() if model.created_at else "",
            confirmed_at=model.confirmed_at.isoformat() if model.confirmed_at else None,
            acknowledged_at=model.acknowledged_at.isoformat() if model.acknowledged_at else None,
            confidence=model.confidence,
            object_type=model.object_type,
            class_name=model.class_name,
            subclass=model.subclass,
            bbox=model.bbox,
            reference_point=model.reference_point,
            trajectory=model.trajectory,
            verification=v_detail,
            description=model.description or ""
        )


# Global singleton event manager instance
event_manager = EventManager()
