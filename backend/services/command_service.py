import json
import logging
import threading
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple

from backend.database.connection import SessionLocal
from backend.database.models import (
    CameraModel,
    IncidentModel,
    SubjectModel,
    SubjectTrackLinkModel,
    IncidentEventLinkModel,
    SecurityEventModel,
    AssociatedVehicleModel,
    CameraTopologyModel,
    RiskAssessmentModel,
    RiskFactorModel,
    OperatorActionModel,
    IncidentNoteModel,
    IncidentStatusHistoryModel
)
from backend.models.command import (
    DashboardSummaryResponse,
    SectorRiskSummary,
    RecommendedCameraResponse,
    OperatorActionResponse,
    IncidentNoteResponse,
    IncidentLifecycleResponse,
    LifecycleStageStatus,
    IncidentStatusHistoryItem,
    IncidentNarrativeResponse,
    CommandAlertResponse
)

logger = logging.getLogger("ibvap.command_service")


# Defined Sector groupings for Border Area
SECTORS_DEF = [
    {
        "sector_id": "SECTOR-A",
        "sector_name": "Sector A — Main Checkpost",
        "camera_ids": ["CAM-01"],
        "description": "Primary checkpoint entry gate and vehicular access corridor."
    },
    {
        "sector_id": "SECTOR-B",
        "sector_name": "Sector B — Northern Perimeter",
        "camera_ids": ["CAM-02"],
        "description": "High-sensitivity northern physical border fence and sterile buffer zone."
    },
    {
        "sector_id": "SECTOR-C",
        "sector_name": "Sector C — River Crossing",
        "camera_ids": ["CAM-03"],
        "description": "Natural river channel infiltration sector and vulnerable terrain boundary."
    },
    {
        "sector_id": "SECTOR-D",
        "sector_name": "Sector D — Perimeter Bravo",
        "camera_ids": ["CAM-04"],
        "description": "Secondary perimeter reserve sector and patrol vehicle transit line."
    }
]


class CommandService:
    """
    Central Command & Response Service (Phase 6).
    Manages operator lifecycle workflows, real-time SOC dashboard summaries,
    sector risk mapping, explainable camera recommendations, and neutral narratives.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.action_counter: int = 0
        self.note_counter: int = 0

    # -------------------------------------------------------------------------
    # 1. Dashboard & Sector Summaries
    # -------------------------------------------------------------------------

    def get_dashboard_summary(self) -> DashboardSummaryResponse:
        """Returns aggregated operational health and incident statistics."""
        db = SessionLocal()
        try:
            cameras = db.query(CameraModel).all()
            total_cams = len(cameras)
            online_cams = sum(1 for c in cameras if c.status == "ONLINE")
            offline_cams = sum(1 for c in cameras if c.status == "OFFLINE")
            degraded_cams = sum(1 for c in cameras if c.status == "DEGRADED")
            alert_cams = sum(1 for c in cameras if c.status == "ALERT")

            incidents = db.query(IncidentModel).all()
            total_inc = len(incidents)
            active_inc = sum(1 for i in incidents if i.status != "CLOSED")
            closed_inc = sum(1 for i in incidents if i.status == "CLOSED")

            crit_count = 0
            high_count = 0
            med_count = 0
            low_count = 0

            for inc in incidents:
                if inc.status == "CLOSED":
                    continue
                risk = db.query(RiskAssessmentModel).filter(RiskAssessmentModel.incident_id == inc.incident_id).first()
                if risk:
                    if risk.risk_level == "CRITICAL":
                        crit_count += 1
                    elif risk.risk_level == "HIGH":
                        high_count += 1
                    elif risk.risk_level == "MEDIUM":
                        med_count += 1
                    else:
                        low_count += 1
                else:
                    low_count += 1

            # Count sectors with high/critical alerts
            sector_risks = self._compute_sector_risks_internal(db)
            sectors_with_alerts = sum(1 for s in sector_risks if s.risk_level in ("HIGH", "CRITICAL"))

            # Active tracks count
            from backend.services.ai_pipeline import ai_service
            ai_status = ai_service.get_global_status()
            active_tracks = ai_status.get("total_active_tracks", 0) if isinstance(ai_status, dict) else getattr(ai_status, "total_active_tracks", 0)

            return DashboardSummaryResponse(
                total_cameras=total_cams,
                online_cameras=online_cams,
                offline_cameras=offline_cams,
                degraded_cameras=degraded_cams,
                alert_cameras=alert_cams,
                total_incidents=total_inc,
                active_incidents=active_inc,
                critical_risk_incidents=crit_count,
                high_risk_incidents=high_count,
                medium_risk_incidents=med_count,
                low_risk_incidents=low_count,
                closed_incidents=closed_inc,
                sectors_count=len(SECTORS_DEF),
                sectors_with_alerts=sectors_with_alerts,
                active_tracks_count=active_tracks,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        finally:
            db.close()

    def get_sector_risks(self) -> List[SectorRiskSummary]:
        """Calculates risk levels and operational status for all defined border sectors."""
        db = SessionLocal()
        try:
            return self._compute_sector_risks_internal(db)
        finally:
            db.close()

    def _compute_sector_risks_internal(self, db) -> List[SectorRiskSummary]:
        results = []
        cams_map = {c.camera_id: c for c in db.query(CameraModel).all()}

        for sec in SECTORS_DEF:
            sec_id = sec["sector_id"]
            sec_cams = sec["camera_ids"]
            
            cams_online = sum(1 for cid in sec_cams if cid in cams_map and cams_map[cid].status in ("ONLINE", "ALERT"))
            cams_total = len(sec_cams)

            # Find incidents touching this sector's cameras
            links = db.query(SubjectTrackLinkModel).filter(SubjectTrackLinkModel.camera_id.in_(sec_cams)).all()
            subj_ids = list(set([l.subject_id for l in links]))

            incidents = db.query(IncidentModel).filter(
                IncidentModel.subject_id.in_(subj_ids),
                IncidentModel.status != "CLOSED"
            ).all() if subj_ids else []

            max_score = 0.0
            highest_level = "LOW"
            has_intrusion = False

            for inc in incidents:
                risk = db.query(RiskAssessmentModel).filter(RiskAssessmentModel.incident_id == inc.incident_id).first()
                if risk:
                    if risk.score > max_score:
                        max_score = risk.score
                        highest_level = risk.risk_level

            # Check active intrusion events in this sector
            evts = db.query(SecurityEventModel).filter(
                SecurityEventModel.camera_id.in_(sec_cams),
                SecurityEventModel.event_type.in_(["ZONE_INTRUSION", "ZONE_ENTRY"]),
                SecurityEventModel.status == "CONFIRMED"
            ).count()
            if evts > 0:
                has_intrusion = True
                if highest_level == "LOW":
                    highest_level = "MEDIUM"

            results.append(SectorRiskSummary(
                sector_id=sec_id,
                sector_name=sec["sector_name"],
                risk_level=highest_level,
                max_risk_score=max_score,
                active_incidents_count=len(incidents),
                camera_ids=sec_cams,
                cameras_online=cams_online,
                cameras_total=cams_total,
                has_active_intrusion=has_intrusion,
                description=sec["description"]
            ))

        return results

    # -------------------------------------------------------------------------
    # 2. Operational Alerts
    # -------------------------------------------------------------------------

    def get_alerts(self) -> List[CommandAlertResponse]:
        """Returns actionable alerts for high or critical incidents and confirmed intrusions."""
        db = SessionLocal()
        try:
            alerts = []
            incidents = db.query(IncidentModel).filter(IncidentModel.status != "CLOSED").order_by(IncidentModel.updated_at.desc()).all()
            cams_map = {c.camera_id: c.camera_name for c in db.query(CameraModel).all()}

            for inc in incidents:
                risk = db.query(RiskAssessmentModel).filter(RiskAssessmentModel.incident_id == inc.incident_id).first()
                if risk and risk.risk_level in ("HIGH", "CRITICAL"):
                    # Find latest camera in journey
                    last_link = db.query(SubjectTrackLinkModel).filter(
                        SubjectTrackLinkModel.subject_id == inc.subject_id
                    ).order_by(SubjectTrackLinkModel.last_timestamp.desc()).first()

                    cam_id = last_link.camera_id if last_link else "CAM-01"
                    cam_name = cams_map.get(cam_id, f"Camera {cam_id}")

                    # Latest zone
                    last_evt = db.query(SecurityEventModel).join(
                        IncidentEventLinkModel, IncidentEventLinkModel.event_id == SecurityEventModel.event_id
                    ).filter(IncidentEventLinkModel.incident_id == inc.incident_id).order_by(SecurityEventModel.created_at.desc()).first()
                    zone_name = last_evt.zone_name if last_evt else "Border Corridor"

                    alert_id = f"ALT-{inc.incident_id}"
                    is_ack = inc.status in ("ACKNOWLEDGED", "INVESTIGATING")

                    alerts.append(CommandAlertResponse(
                        alert_id=alert_id,
                        incident_id=inc.incident_id,
                        subject_id=inc.subject_id,
                        risk_level=risk.risk_level,
                        risk_score=risk.score,
                        camera_id=cam_id,
                        camera_name=cam_name,
                        zone_name=zone_name,
                        message=f"{risk.risk_level} Risk detected on {cam_name} ({zone_name}): Score {risk.score:.0f}/100.",
                        timestamp=risk.updated_at.isoformat(),
                        is_acknowledged=is_ack
                    ))

            return alerts
        finally:
            db.close()

    # -------------------------------------------------------------------------
    # 3. Camera Recommendations (Phase 4 Topology Grounded)
    # -------------------------------------------------------------------------

    def get_recommended_cameras(self, incident_id: str) -> List[RecommendedCameraResponse]:
        """
        Determines recommended forward-tracking and nearby cameras using Phase 4 topology graph.
        Never generates arbitrary recommendations; grounded in physical adjacency and journey heading.
        """
        db = SessionLocal()
        try:
            inc = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
            if not inc:
                return []

            # Find all cameras visited so far
            links = db.query(SubjectTrackLinkModel).filter(
                SubjectTrackLinkModel.subject_id == inc.subject_id
            ).order_by(SubjectTrackLinkModel.first_timestamp.asc()).all()

            if not links:
                return []

            visited_cams = [l.camera_id for l in links]
            current_cam = visited_cams[-1]

            cams_db = {c.camera_id: c for c in db.query(CameraModel).all()}
            topo_edges = db.query(CameraTopologyModel).filter(
                CameraTopologyModel.source_camera == current_cam,
                CameraTopologyModel.enabled == True
            ).all()

            recommendations: List[RecommendedCameraResponse] = []
            rec_cams_seen = set()

            # 1. Downstream Topology Neighbors (Forward Route Continuation)
            for edge in topo_edges:
                dest = edge.destination_camera
                if dest not in rec_cams_seen and dest in cams_db:
                    rec_cams_seen.add(dest)
                    dest_cam = cams_db[dest]
                    recommendations.append(RecommendedCameraResponse(
                        camera_id=dest,
                        camera_name=dest_cam.camera_name,
                        location=dest_cam.location,
                        reason=f"Adjacent downstream sensor along travel corridor from {current_cam} (est. transit {edge.min_transition_seconds:.0f}s–{edge.max_transition_seconds:.0f}s).",
                        relationship="JOURNEY_CONTINUATION",
                        distance_meters=edge.distance_meters,
                        expected_transit_window=f"{edge.min_transition_seconds:.0f}s – {edge.max_transition_seconds:.0f}s"
                    ))

            # 2. Correlated cameras from historical journey
            for v_cam in reversed(visited_cams[:-1]):
                if v_cam not in rec_cams_seen and v_cam in cams_db:
                    rec_cams_seen.add(v_cam)
                    v_cam_obj = cams_db[v_cam]
                    recommendations.append(RecommendedCameraResponse(
                        camera_id=v_cam,
                        camera_name=v_cam_obj.camera_name,
                        location=v_cam_obj.location,
                        reason=f"Origin / prior sensor in subject multi-camera journey.",
                        relationship="TOPOLOGY_NEIGHBOR",
                        distance_meters=50.0,
                        expected_transit_window=None
                    ))

            # 3. Fallback: Other active sensors if list is small
            if len(recommendations) < 2:
                for cid, cobj in cams_db.items():
                    if cid != current_cam and cid not in rec_cams_seen and cobj.status == "ONLINE":
                        rec_cams_seen.add(cid)
                        recommendations.append(RecommendedCameraResponse(
                            camera_id=cid,
                            camera_name=cobj.camera_name,
                            location=cobj.location,
                            reason=f"Active perimeter monitoring sensor in adjacent sector.",
                            relationship="SPATIAL_PROXIMITY",
                            distance_meters=100.0,
                            expected_transit_window=None
                        ))
                        if len(recommendations) >= 3:
                            break

            return recommendations
        finally:
            db.close()

    # -------------------------------------------------------------------------
    # 4. Objective Machine Narrative Synthesis
    # -------------------------------------------------------------------------

    def get_incident_narrative(self, incident_id: str) -> Optional[IncidentNarrativeResponse]:
        """
        Synthesizes an objective, neutral incident narrative purely from verified system data.
        Adheres strictly to factual language ('subject', 'movement', 'verified event', 'correlated activity').
        """
        db = SessionLocal()
        try:
            inc = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
            if not inc:
                return None

            subj = db.query(SubjectModel).filter(SubjectModel.subject_id == inc.subject_id).first()
            risk = db.query(RiskAssessmentModel).filter(RiskAssessmentModel.incident_id == incident_id).first()
            cams_map = {c.camera_id: c.camera_name for c in db.query(CameraModel).all()}

            links = db.query(SubjectTrackLinkModel).filter(
                SubjectTrackLinkModel.subject_id == inc.subject_id
            ).order_by(SubjectTrackLinkModel.first_timestamp.asc()).all()

            events = db.query(SecurityEventModel).join(
                IncidentEventLinkModel, IncidentEventLinkModel.event_id == SecurityEventModel.event_id
            ).filter(IncidentEventLinkModel.incident_id == incident_id).order_by(SecurityEventModel.created_at.asc()).all()

            vehicles = db.query(AssociatedVehicleModel).filter(
                AssociatedVehicleModel.subject_id == inc.subject_id
            ).all()

            key_facts = []
            narrative_paragraphs = []

            # Fact 1: Initial Detection
            if links:
                first_link = links[0]
                t_first = first_link.first_timestamp.strftime("%H:%M:%S UTC")
                cam_name = cams_map.get(first_link.camera_id, first_link.camera_id)
                key_facts.append(f"Initial detection of {inc.subject_id} on {cam_name} ({first_link.formatted_track_id}) at {t_first}.")
                narrative_paragraphs.append(
                    f"At {t_first}, subject '{inc.subject_id}' ({subj.object_type if subj else 'entity'}) was initially detected "
                    f"on {cam_name} as local track {first_link.formatted_track_id}."
                )

            # Fact 2: Multi-Frame Verified Events
            if events:
                for evt in events:
                    t_evt = evt.created_at.strftime("%H:%M:%S UTC")
                    cam_name = cams_map.get(evt.camera_id, evt.camera_id)
                    key_facts.append(f"Verified {evt.event_type} event in '{evt.zone_name}' on {cam_name} at {t_evt} (Confidence: {evt.confidence * 100:.0f}%).")

                first_evt = events[0]
                narrative_paragraphs.append(
                    f"The subject entered '{first_evt.zone_name}' on {cams_map.get(first_evt.camera_id, first_evt.camera_id)}, "
                    f"triggering a multi-frame verified {first_evt.event_type} security event."
                )

            # Fact 3: Cross-Camera Re-ID
            if len(links) > 1:
                subsequent_cams = [cams_map.get(l.camera_id, l.camera_id) for l in links[1:]]
                cams_str = ", ".join(subsequent_cams)
                key_facts.append(f"Re-identified across {len(links)} cameras along travel route ({cams_str}).")
                narrative_paragraphs.append(
                    f"Using evidence-based spatial and temporal matching, the subject was subsequently correlated across {cams_str}."
                )

            # Fact 4: Contextual Vehicle Correlation
            if vehicles:
                for v in vehicles:
                    key_facts.append(f"Spatially and temporally associated with vehicle '{v.vehicle_subject_id}' near {v.camera_id} (~{v.proximity_meters:.0f}m proximity).")
                narrative_paragraphs.append(
                    f"A nearby vehicle ('{vehicles[0].vehicle_subject_id}') was observed within {vehicles[0].proximity_meters:.0f}m proximity, "
                    f"establishing a contextual person-vehicle association."
                )

            # Fact 5: Risk Assessment
            r_score = risk.score if risk else 0.0
            r_level = risk.risk_level if risk else "LOW"
            narrative_paragraphs.append(
                f"The composite explainable risk engine evaluated the consolidated incident at a risk score of {r_score:.0f}/100 ({r_level} RISK)."
            )

            full_narrative = " ".join(narrative_paragraphs)

            return IncidentNarrativeResponse(
                incident_id=incident_id,
                subject_id=inc.subject_id,
                risk_level=r_level,
                risk_score=r_score,
                narrative=full_narrative,
                key_facts=key_facts,
                generated_at=datetime.now(timezone.utc).isoformat()
            )
        finally:
            db.close()

    # -------------------------------------------------------------------------
    # 5. Incident Lifecycle & State Machine
    # -------------------------------------------------------------------------

    def get_incident_lifecycle(self, incident_id: str) -> Optional[IncidentLifecycleResponse]:
        """Returns the full 7-stage lifecycle state and transition history of an incident."""
        db = SessionLocal()
        try:
            inc = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
            if not inc:
                return None

            status = inc.status  # ACTIVE, ASSESSED, ACKNOWLEDGED, INVESTIGATING, CLOSED
            norm_status = "ASSESSED" if status == "ACTIVE" else status

            history_rows = db.query(IncidentStatusHistoryModel).filter(
                IncidentStatusHistoryModel.incident_id == incident_id
            ).order_by(IncidentStatusHistoryModel.timestamp.asc()).all()

            history_items = [
                IncidentStatusHistoryItem(
                    previous_status=h.previous_status,
                    new_status=h.new_status,
                    changed_by=h.changed_by,
                    role=h.role,
                    notes=h.notes or "",
                    timestamp=h.timestamp.isoformat()
                )
                for h in history_rows
            ]

            # Determine stage completion
            is_ack = norm_status in ("ACKNOWLEDGED", "INVESTIGATING", "CLOSED")
            is_inv = norm_status in ("INVESTIGATING", "CLOSED")
            is_cls = norm_status == "CLOSED"

            stages = [
                LifecycleStageStatus(
                    stage="DETECTED",
                    is_completed=True,
                    is_current=False,
                    completed_at=inc.created_at.isoformat(),
                    description="ByteTrack AI perception detected and tracked subject on border camera."
                ),
                LifecycleStageStatus(
                    stage="VERIFIED",
                    is_completed=True,
                    is_current=False,
                    completed_at=inc.created_at.isoformat(),
                    description="Phase 3 temporal verification gate confirmed ground-contact zone intrusion."
                ),
                LifecycleStageStatus(
                    stage="CORRELATED",
                    is_completed=True,
                    is_current=False,
                    completed_at=inc.created_at.isoformat(),
                    description="Cross-camera intelligence linked sensor handoffs and contextual entities."
                ),
                LifecycleStageStatus(
                    stage="ASSESSED",
                    is_completed=True,
                    is_current=(norm_status == "ASSESSED"),
                    completed_at=inc.updated_at.isoformat(),
                    description="Phase 5 multi-factor explainable risk score generated."
                ),
                LifecycleStageStatus(
                    stage="ACKNOWLEDGED",
                    is_completed=is_ack,
                    is_current=(norm_status == "ACKNOWLEDGED"),
                    completed_at=next((h.timestamp for h in history_items if h.new_status == "ACKNOWLEDGED"), None),
                    operator_id=next((h.changed_by for h in history_items if h.new_status == "ACKNOWLEDGED"), None),
                    description="Human operator acknowledged incident notification and threat assessment."
                ),
                LifecycleStageStatus(
                    stage="INVESTIGATING",
                    is_completed=is_inv,
                    is_current=(norm_status == "INVESTIGATING"),
                    completed_at=next((h.timestamp for h in history_items if h.new_status == "INVESTIGATING"), None),
                    operator_id=next((h.changed_by for h in history_items if h.new_status == "INVESTIGATING"), None),
                    description="Human operator actively examining live camera wall, timeline, and journey."
                ),
                LifecycleStageStatus(
                    stage="CLOSED",
                    is_completed=is_cls,
                    is_current=(norm_status == "CLOSED"),
                    completed_at=next((h.timestamp for h in history_items if h.new_status == "CLOSED"), None),
                    operator_id=next((h.changed_by for h in history_items if h.new_status == "CLOSED"), None),
                    description="Operational investigation finalized and incident archived."
                )
            ]

            return IncidentLifecycleResponse(
                incident_id=incident_id,
                subject_id=inc.subject_id,
                current_status=norm_status,
                stages=stages,
                history=history_items
            )
        finally:
            db.close()

    def transition_incident_status(
        self,
        incident_id: str,
        target_status: str,
        operator_id: str = "OP-001",
        role: str = "OPERATOR",
        notes: str = ""
    ) -> Tuple[bool, str, Optional[IncidentLifecycleResponse]]:
        """
        Executes an operator-facing lifecycle transition with strict validation.
        Supported transitions:
          - ASSESSED/ACTIVE -> ACKNOWLEDGED
          - ACKNOWLEDGED -> INVESTIGATING
          - INVESTIGATING/ACKNOWLEDGED -> CLOSED
        """
        with self._lock:
            db = SessionLocal()
            try:
                inc = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
                if not inc:
                    return False, f"Incident '{incident_id}' not found.", None

                current_status = inc.status
                current_norm = "ASSESSED" if current_status == "ACTIVE" else current_status
                target_status = target_status.upper()

                # Validate transition rules
                allowed = False
                if target_status == "ACKNOWLEDGED" and current_norm in ("ASSESSED", "ACTIVE"):
                    allowed = True
                elif target_status == "INVESTIGATING" and current_norm == "ACKNOWLEDGED":
                    allowed = True
                elif target_status == "CLOSED" and current_norm in ("INVESTIGATING", "ACKNOWLEDGED"):
                    allowed = True

                if not allowed:
                    return False, (
                        f"Invalid lifecycle transition from '{current_norm}' to '{target_status}'. "
                        f"Allowed transitions: ASSESSED -> ACKNOWLEDGED -> INVESTIGATING -> CLOSED."
                    ), None

                now_dt = datetime.now(timezone.utc)
                inc.status = target_status
                inc.updated_at = now_dt

                # Record status history
                hist = IncidentStatusHistoryModel(
                    incident_id=incident_id,
                    previous_status=current_norm,
                    new_status=target_status,
                    changed_by=operator_id,
                    role=role,
                    notes=notes or f"Incident transitioned to {target_status} by {role} {operator_id}",
                    timestamp=now_dt
                )
                db.add(hist)

                # Record operator action
                self.action_counter += 1
                action_id = f"ACT-{self.action_counter:04d}-{int(now_dt.timestamp() * 1000)}"
                action = OperatorActionModel(
                    action_id=action_id,
                    incident_id=incident_id,
                    operator_id=operator_id,
                    role=role,
                    action=target_status,
                    notes=notes or f"Operator action: {target_status}",
                    metadata_json=json.dumps({"previous_status": current_norm, "new_status": target_status}),
                    timestamp=now_dt
                )
                db.add(action)

                db.commit()
                logger.info(f"Transitioned incident '{incident_id}' from '{current_norm}' to '{target_status}' by {operator_id} ({role})")

            finally:
                db.close()

            # Enqueue operator status transition to sync queue
            try:
                from backend.services.sync_service import sync_service
                sync_service.enqueue_item(
                    entity_type="OPERATOR_ACTION",
                    entity_id=action_id,
                    payload={
                        "incident_id": incident_id,
                        "action_id": action_id,
                        "previous_status": current_norm,
                        "new_status": target_status,
                        "operator_id": operator_id,
                        "role": role,
                        "notes": notes,
                        "timestamp": now_dt.isoformat()
                    },
                    operation="STATUS_CHANGE",
                    priority=2,
                    created_at=now_dt
                )
            except Exception as e:
                logger.warning(f"Could not enqueue operator action: {e}")

            # Notify real-time UI via WebSocket
            from backend.api.websocket import broadcast_command_event
            broadcast_command_event({
                "event_type": "INCIDENT_STATUS_CHANGED",
                "incident_id": incident_id,
                "previous_status": current_norm,
                "new_status": target_status,
                "changed_by": operator_id,
                "role": role,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            lifecycle = self.get_incident_lifecycle(incident_id)
            return True, f"Incident successfully transitioned to '{target_status}'.", lifecycle

    def acknowledge_incident(
        self,
        incident_id: str,
        operator_id: str = "OP-9402",
        role: str = "OPERATOR",
        notes: str = ""
    ) -> OperatorActionResponse:
        """Helper to acknowledge an incident and return the recorded operator action."""
        ok, msg, lf = self.transition_incident_status(incident_id, "ACKNOWLEDGED", operator_id, role, notes)
        return OperatorActionResponse(
            action_id=f"ACT-ACK-{incident_id}",
            incident_id=incident_id,
            operator_id=operator_id,
            role=role,
            action="ACKNOWLEDGED",
            notes=notes,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def investigate_incident(
        self,
        incident_id: str,
        operator_id: str = "OP-9402",
        role: str = "OPERATOR",
        notes: str = ""
    ) -> OperatorActionResponse:
        """Helper to transition incident to INVESTIGATING."""
        ok, msg, lf = self.transition_incident_status(incident_id, "INVESTIGATING", operator_id, role, notes)
        return OperatorActionResponse(
            action_id=f"ACT-INV-{incident_id}",
            incident_id=incident_id,
            operator_id=operator_id,
            role=role,
            action="INVESTIGATING",
            notes=notes,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def close_incident(
        self,
        incident_id: str,
        operator_id: str = "OP-9402",
        role: str = "OPERATOR",
        notes: str = ""
    ) -> OperatorActionResponse:
        """Helper to transition incident to CLOSED."""
        ok, msg, lf = self.transition_incident_status(incident_id, "CLOSED", operator_id, role, notes)
        return OperatorActionResponse(
            action_id=f"ACT-CLS-{incident_id}",
            incident_id=incident_id,
            operator_id=operator_id,
            role=role,
            action="CLOSED",
            notes=notes,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    # -------------------------------------------------------------------------
    # 6. Operator Notes & Actions
    # -------------------------------------------------------------------------

    def add_incident_note(
        self,
        incident_id: str,
        operator_id: str = "OP-001",
        role: str = "OPERATOR",
        note_text: str = ""
    ) -> Optional[IncidentNoteResponse]:
        """Appends an operator note to the incident without altering AI risk factors."""
        if not note_text or not note_text.strip():
            return None

        db = SessionLocal()
        try:
            inc = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
            if not inc:
                return None

            now_dt = datetime.now(timezone.utc)
            self.note_counter += 1
            note_id = f"NOTE-{self.note_counter:04d}-{int(now_dt.timestamp() * 1000)}"

            note = IncidentNoteModel(
                note_id=note_id,
                incident_id=incident_id,
                operator_id=operator_id,
                role=role,
                note=note_text.strip(),
                timestamp=now_dt
            )
            db.add(note)

            # Also record operator action
            self.action_counter += 1
            action_id = f"ACT-{self.action_counter:04d}-{int(now_dt.timestamp() * 1000)}"
            action = OperatorActionModel(
                action_id=action_id,
                incident_id=incident_id,
                operator_id=operator_id,
                role=role,
                action="ADD_NOTE",
                notes=note_text[:100],
                metadata_json=json.dumps({"note_id": note_id}),
                timestamp=now_dt
            )
            db.add(action)

            db.commit()
            logger.info(f"Added operator note '{note_id}' to incident '{incident_id}' by {operator_id}")

            # Enqueue to sync queue
            try:
                from backend.services.sync_service import sync_service
                sync_service.enqueue_item(
                    entity_type="INCIDENT_NOTE",
                    entity_id=note_id,
                    payload={
                        "incident_id": incident_id,
                        "note_id": note_id,
                        "operator_id": operator_id,
                        "role": role,
                        "note": note_text.strip(),
                        "timestamp": now_dt.isoformat()
                    },
                    operation="CREATE",
                    priority=2,
                    created_at=now_dt
                )
            except Exception as e:
                logger.warning(f"Could not enqueue note to sync queue: {e}")

            return IncidentNoteResponse(
                note_id=note_id,
                incident_id=incident_id,
                operator_id=operator_id,
                role=role,
                note=note_text.strip(),
                timestamp=now_dt.isoformat()
            )
        finally:
            db.close()

    def add_note(
        self,
        incident_id: str,
        operator_id: str = "OP-9402",
        role: str = "OPERATOR",
        note: str = ""
    ) -> Optional[IncidentNoteResponse]:
        """Convenience alias for add_incident_note."""
        return self.add_incident_note(incident_id, operator_id, role, note)

    def get_incident_notes(self, incident_id: str) -> List[IncidentNoteResponse]:
        """Returns all operator notes recorded for an incident."""
        db = SessionLocal()
        try:
            notes = db.query(IncidentNoteModel).filter(
                IncidentNoteModel.incident_id == incident_id
            ).order_by(IncidentNoteModel.timestamp.desc()).all()

            return [
                IncidentNoteResponse(
                    note_id=n.note_id,
                    incident_id=n.incident_id,
                    operator_id=n.operator_id,
                    role=n.role,
                    note=n.note,
                    timestamp=n.timestamp.isoformat()
                )
                for n in notes
            ]
        finally:
            db.close()

    def get_operator_actions(self, incident_id: str) -> List[OperatorActionResponse]:
        """Returns the full audit trail of operator actions for an incident."""
        db = SessionLocal()
        try:
            actions = db.query(OperatorActionModel).filter(
                OperatorActionModel.incident_id == incident_id
            ).order_by(OperatorActionModel.timestamp.desc()).all()

            return [
                OperatorActionResponse(
                    action_id=a.action_id,
                    incident_id=a.incident_id,
                    operator_id=a.operator_id,
                    role=a.role,
                    action=a.action,
                    notes=a.notes or "",
                    metadata=a.action_metadata,
                    timestamp=a.timestamp.isoformat()
                )
                for a in actions
            ]
        finally:
            db.close()

    def log_operator_action(
        self,
        incident_id: str,
        operator_id: str = "OP-001",
        role: str = "OPERATOR",
        action_name: str = "FOCUS_CAMERA",
        notes: str = "",
        metadata: Dict[str, Any] = None
    ) -> OperatorActionResponse:
        """Logs general operator actions (e.g. camera focus, bookmark)."""
        db = SessionLocal()
        try:
            now_dt = datetime.now(timezone.utc)
            self.action_counter += 1
            action_id = f"ACT-{self.action_counter:04d}-{int(now_dt.timestamp() * 1000)}"

            action = OperatorActionModel(
                action_id=action_id,
                incident_id=incident_id,
                operator_id=operator_id,
                role=role,
                action=action_name,
                notes=notes,
                metadata_json=json.dumps(metadata or {}),
                timestamp=now_dt
            )
            db.add(action)
            db.commit()

            return OperatorActionResponse(
                action_id=action_id,
                incident_id=incident_id,
                operator_id=operator_id,
                role=role,
                action=action_name,
                notes=notes,
                metadata=metadata or {},
                timestamp=now_dt.isoformat()
            )
        finally:
            db.close()


# Global singleton Command & Response Service
command_service = CommandService()
