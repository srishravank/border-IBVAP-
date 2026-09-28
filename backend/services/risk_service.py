import json
import logging
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta

from backend.config import settings
from backend.database.connection import SessionLocal
from backend.database.models import (
    IncidentModel,
    SubjectModel,
    IncidentEventLinkModel,
    SecurityEventModel,
    ZoneModel,
    SubjectTrackLinkModel,
    AssociatedVehicleModel,
    RiskAssessmentModel,
    RiskFactorModel,
    RiskHistoryModel,
    RiskConfigurationModel,
    CameraModel
)
from backend.models.risk import (
    RiskAssessmentResponse,
    RiskFactorResponse,
    RiskHistoryResponse,
    RiskConfigurationResponse,
    UpdateRiskConfigurationPayload,
    RiskSummaryResponse,
    IncidentIntelligenceResponse
)
from intelligence.risk.risk_aggregator import RiskAggregator, AggregatedRiskAssessment
from intelligence.risk.factor_base import RiskFactorResult
from intelligence.risk.explanation_generator import ExplanationGenerator

logger = logging.getLogger("ibvap.risk_service")


class RiskService:
    """
    Central Risk Engine Management Service for IBVAP 2.0 (Phase 5).
    Evaluates multi-factor explainable risk for incidents, manages persistent risk history,
    versioned configuration, and generates the standardized Phase 6 Intelligence Object.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.aggregator = RiskAggregator()
        self.last_evaluated: Dict[str, float] = {}  # incident_id -> timestamp
        self.assessment_counter: int = 0
        self.config_counter: int = 1

    def evaluate_incident(self, incident_id: str, force: bool = False) -> Optional[RiskAssessmentResponse]:
        """
        Executes explainable multi-factor risk assessment for a specific incident.
        Updates persistent database records and appends to risk history.
        """
        with self._lock:
            now_t = datetime.now(timezone.utc).timestamp()
            last_t = self.last_evaluated.get(incident_id, 0.0)

            if not force and (now_t - last_t) < settings.RISK_ASSESSMENT_COOLDOWN_SECONDS:
                return self.get_incident_risk(incident_id)

            self.last_evaluated[incident_id] = now_t

            db = SessionLocal()
            try:
                # 1. Fetch Incident and Subject
                inc = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
                if not inc:
                    logger.warning(f"Cannot evaluate risk: Incident '{incident_id}' not found.")
                    return None

                subj = db.query(SubjectModel).filter(SubjectModel.subject_id == inc.subject_id).first()
                if not subj:
                    logger.warning(f"Subject '{inc.subject_id}' not found for incident '{incident_id}'.")

                # 2. Fetch linked verified events
                event_links = db.query(IncidentEventLinkModel).filter(
                    IncidentEventLinkModel.incident_id == incident_id
                ).order_by(IncidentEventLinkModel.sequence_number.asc()).all()
                event_ids = [l.event_id for l in event_links]

                events = db.query(SecurityEventModel).filter(
                    SecurityEventModel.event_id.in_(event_ids)
                ).all() if event_ids else []

                # 3. Fetch zones
                zone_ids = [e.zone_id for e in events if e.zone_id]
                zones = db.query(ZoneModel).all()
                zones_map = {z.zone_id: z for z in zones}

                # 4. Fetch subject track journey
                journey = db.query(SubjectTrackLinkModel).filter(
                    SubjectTrackLinkModel.subject_id == inc.subject_id
                ).order_by(SubjectTrackLinkModel.first_timestamp.asc()).all()

                # 5. Fetch associated vehicles
                vehicles = db.query(AssociatedVehicleModel).filter(
                    AssociatedVehicleModel.subject_id == inc.subject_id
                ).all()

                # 6. Fetch active risk configuration
                active_cfg = db.query(RiskConfigurationModel).filter(
                    RiskConfigurationModel.is_active == True
                ).first()

                config_dict = {}
                if active_cfg:
                    config_dict = {
                        "config_version": active_cfg.config_version,
                        "weights": active_cfg.weights,
                        "thresholds": active_cfg.thresholds,
                        "night_start_time": active_cfg.night_start_time,
                        "night_end_time": active_cfg.night_end_time,
                        "enabled_factors": active_cfg.enabled_factors
                    }

                # 7. Build context and assess
                incident_context = {
                    "incident": inc,
                    "subject": subj,
                    "events": events,
                    "zones": zones_map,
                    "journey": journey,
                    "associated_vehicles": vehicles
                }

                assessment: AggregatedRiskAssessment = self.aggregator.assess_incident(
                    incident_context=incident_context,
                    config=config_dict
                )

                # 8. Persist assessment in DB
                existing_assessment = db.query(RiskAssessmentModel).filter(
                    RiskAssessmentModel.incident_id == incident_id
                ).first()

                now_dt = datetime.now(timezone.utc)
                if not existing_assessment:
                    while True:
                        self.assessment_counter += 1
                        assessment_id = f"RSK-{self.assessment_counter:04d}"
                        if not db.query(RiskAssessmentModel).filter(RiskAssessmentModel.assessment_id == assessment_id).first():
                            break
                    existing_assessment = RiskAssessmentModel(
                        assessment_id=assessment_id,
                        incident_id=incident_id,
                        subject_id=inc.subject_id,
                        score=assessment.score,
                        risk_level=assessment.risk_level,
                        confidence=assessment.confidence,
                        config_version=assessment.config_version,
                        explanation=assessment.explanation,
                        created_at=now_dt,
                        updated_at=now_dt
                    )
                    db.add(existing_assessment)
                else:
                    assessment_id = existing_assessment.assessment_id
                    existing_assessment.score = assessment.score
                    existing_assessment.risk_level = assessment.risk_level
                    existing_assessment.confidence = assessment.confidence
                    existing_assessment.config_version = assessment.config_version
                    existing_assessment.explanation = assessment.explanation
                    existing_assessment.updated_at = now_dt

                # 9. Update factors table
                db.query(RiskFactorModel).filter(RiskFactorModel.assessment_id == assessment_id).delete()
                
                factor_responses = []
                factors_summary = []

                for idx, f in enumerate(assessment.factors):
                    f_id = f"{assessment_id}-F{idx+1:02d}"
                    factor_orm = RiskFactorModel(
                        factor_id=f_id,
                        assessment_id=assessment_id,
                        factor_type=f.factor_type,
                        contribution=f.contribution,
                        confidence=f.confidence,
                        evidence=f.evidence,
                        source_event_ids_json=json.dumps(f.source_event_ids),
                        metadata_json=json.dumps(f.metadata),
                        created_at=now_dt
                    )
                    db.add(factor_orm)

                    factor_responses.append(RiskFactorResponse(
                        factor_id=f_id,
                        factor_type=f.factor_type,
                        factor_name=f.factor_name,
                        contribution=f.contribution,
                        confidence=f.confidence,
                        evidence=f.evidence,
                        source_event_ids=f.source_event_ids,
                        metadata=f.metadata,
                        is_available=f.is_available
                    ))

                    if f.is_available and f.contribution > 0:
                        factors_summary.append({
                            "type": f.factor_type,
                            "name": f.factor_name,
                            "contribution": f.contribution,
                            "evidence": f.evidence
                        })

                # 10. Record History entry
                history_id = f"HIST-{assessment_id}-{int(now_dt.timestamp() * 1000000)}"
                history_entry = RiskHistoryModel(
                    history_id=history_id,
                    incident_id=incident_id,
                    assessment_id=assessment_id,
                    score=assessment.score,
                    risk_level=assessment.risk_level,
                    factors_summary_json=json.dumps(factors_summary),
                    timestamp=now_dt
                )
                db.add(history_entry)

                db.commit()
                logger.info(f"Evaluated Risk for Incident '{incident_id}': {assessment.risk_level} (Score: {assessment.score}/100)")

                return RiskAssessmentResponse(
                    assessment_id=assessment_id,
                    incident_id=incident_id,
                    subject_id=inc.subject_id,
                    score=assessment.score,
                    risk_level=assessment.risk_level,
                    confidence=assessment.confidence,
                    config_version=assessment.config_version,
                    explanation=assessment.explanation,
                    factors=factor_responses,
                    evidence_checklist=assessment.evidence_checklist,
                    created_at=existing_assessment.created_at.isoformat(),
                    updated_at=existing_assessment.updated_at.isoformat()
                )

            except Exception as e:
                db.rollback()
                logger.error(f"Error evaluating risk for incident '{incident_id}': {e}", exc_info=True)
                return None
            finally:
                db.close()

    def get_incident_risk(self, incident_id: str) -> Optional[RiskAssessmentResponse]:
        """Fetches the latest stored risk assessment for an incident."""
        db = SessionLocal()
        try:
            ra = db.query(RiskAssessmentModel).filter(RiskAssessmentModel.incident_id == incident_id).first()
            if not ra:
                # Attempt to evaluate if incident exists but assessment hasn't run yet
                db.close()
                return self.evaluate_incident(incident_id, force=True)

            factors_orm = db.query(RiskFactorModel).filter(RiskFactorModel.assessment_id == ra.assessment_id).all()
            
            factors = [
                RiskFactorResponse(
                    factor_id=f.factor_id,
                    factor_type=f.factor_type,
                    factor_name=f.factor_type.replace("_", " ").title(),
                    contribution=f.contribution,
                    confidence=f.confidence,
                    evidence=f.evidence,
                    source_event_ids=f.source_event_ids,
                    metadata=f.factor_metadata,
                    is_available=True
                )
                for f in factors_orm
            ]

            checklist = ExplanationGenerator.generate_evidence_checklist([
                RiskFactorResult(
                    factor_type=f.factor_type,
                    factor_name=f.factor_type.replace("_", " ").title(),
                    raw_score=f.contribution / 25.0,  # approximate
                    contribution=f.contribution,
                    confidence=f.confidence,
                    evidence=f.evidence,
                    source_event_ids=f.source_event_ids
                )
                for f in factors_orm
            ])

            return RiskAssessmentResponse(
                assessment_id=ra.assessment_id,
                incident_id=ra.incident_id,
                subject_id=ra.subject_id,
                score=ra.score,
                risk_level=ra.risk_level,
                confidence=ra.confidence,
                config_version=ra.config_version,
                explanation=ra.explanation,
                factors=factors,
                evidence_checklist=checklist,
                created_at=ra.created_at.isoformat(),
                updated_at=ra.updated_at.isoformat()
            )
        finally:
            db.close()

    def get_incident_risk_history(self, incident_id: str) -> List[RiskHistoryResponse]:
        """Returns chronological risk history entries for an incident."""
        db = SessionLocal()
        try:
            histories = db.query(RiskHistoryModel).filter(
                RiskHistoryModel.incident_id == incident_id
            ).order_by(RiskHistoryModel.timestamp.asc()).all()

            return [
                RiskHistoryResponse(
                    history_id=h.history_id,
                    incident_id=h.incident_id,
                    assessment_id=h.assessment_id,
                    score=h.score,
                    risk_level=h.risk_level,
                    factors_summary=h.factors_summary,
                    timestamp=h.timestamp.isoformat()
                )
                for h in histories
            ]
        finally:
            db.close()

    def get_active_config(self) -> RiskConfigurationResponse:
        """Retrieves active risk configuration."""
        db = SessionLocal()
        try:
            cfg = db.query(RiskConfigurationModel).filter(RiskConfigurationModel.is_active == True).first()
            if not cfg:
                # Fallback to defaults
                return RiskConfigurationResponse(
                    config_version="v1.0.0",
                    weights={
                        "zone": settings.RISK_WEIGHT_ZONE,
                        "fence": settings.RISK_WEIGHT_FENCE,
                        "night": settings.RISK_WEIGHT_NIGHT,
                        "trajectory": settings.RISK_WEIGHT_TRAJECTORY,
                        "cross_camera": settings.RISK_WEIGHT_CROSS_CAMERA,
                        "vehicle": settings.RISK_WEIGHT_VEHICLE,
                        "behaviour": settings.RISK_WEIGHT_BEHAVIOUR
                    },
                    thresholds={
                        "low_max": settings.RISK_LOW_MAX,
                        "medium_max": settings.RISK_MEDIUM_MAX,
                        "high_max": settings.RISK_HIGH_MAX
                    },
                    night_start_time=settings.NIGHT_START_TIME,
                    night_end_time=settings.NIGHT_END_TIME,
                    enabled_factors=[
                        "ZONE_SENSITIVITY",
                        "FENCE_CROSSING",
                        "NIGHT_MOVEMENT",
                        "TRAJECTORY",
                        "CROSS_CAMERA_JOURNEY",
                        "RELATED_VEHICLE_ACTIVITY"
                    ],
                    is_active=True,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    updated_at=datetime.now(timezone.utc).isoformat()
                )

            return RiskConfigurationResponse(
                config_version=cfg.config_version,
                weights=cfg.weights,
                thresholds=cfg.thresholds,
                night_start_time=cfg.night_start_time,
                night_end_time=cfg.night_end_time,
                enabled_factors=cfg.enabled_factors,
                is_active=cfg.is_active,
                created_at=cfg.created_at.isoformat(),
                updated_at=cfg.updated_at.isoformat()
            )
        finally:
            db.close()

    def update_config(self, payload: UpdateRiskConfigurationPayload) -> RiskConfigurationResponse:
        """Creates a new active versioned configuration preset."""
        db = SessionLocal()
        try:
            # Deactivate current active configs
            active_configs = db.query(RiskConfigurationModel).filter(RiskConfigurationModel.is_active == True).all()
            for c in active_configs:
                c.is_active = False

            curr_cfg = active_configs[0] if active_configs else None

            total_cfgs = db.query(RiskConfigurationModel).count()
            self.config_counter = max(self.config_counter + 1, total_cfgs + 1)
            new_version = f"v1.{self.config_counter}.0"

            weights = payload.weights or (curr_cfg.weights if curr_cfg else {
                "zone": settings.RISK_WEIGHT_ZONE,
                "fence": settings.RISK_WEIGHT_FENCE,
                "night": settings.RISK_WEIGHT_NIGHT,
                "trajectory": settings.RISK_WEIGHT_TRAJECTORY,
                "cross_camera": settings.RISK_WEIGHT_CROSS_CAMERA,
                "vehicle": settings.RISK_WEIGHT_VEHICLE,
                "behaviour": settings.RISK_WEIGHT_BEHAVIOUR
            })

            thresholds = payload.thresholds or (curr_cfg.thresholds if curr_cfg else {
                "low_max": settings.RISK_LOW_MAX,
                "medium_max": settings.RISK_MEDIUM_MAX,
                "high_max": settings.RISK_HIGH_MAX
            })

            night_start = payload.night_start_time or (curr_cfg.night_start_time if curr_cfg else settings.NIGHT_START_TIME)
            night_end = payload.night_end_time or (curr_cfg.night_end_time if curr_cfg else settings.NIGHT_END_TIME)
            enabled = payload.enabled_factors or (curr_cfg.enabled_factors if curr_cfg else [
                "ZONE_SENSITIVITY",
                "FENCE_CROSSING",
                "NIGHT_MOVEMENT",
                "TRAJECTORY",
                "CROSS_CAMERA_JOURNEY",
                "RELATED_VEHICLE_ACTIVITY"
            ])

            now_dt = datetime.now(timezone.utc)
            new_cfg = RiskConfigurationModel(
                config_version=new_version,
                weights_json=json.dumps(weights),
                thresholds_json=json.dumps(thresholds),
                night_start_time=night_start,
                night_end_time=night_end,
                enabled_factors_json=json.dumps(enabled),
                is_active=True,
                created_at=now_dt,
                updated_at=now_dt
            )
            db.add(new_cfg)
            db.commit()

            logger.info(f"Created active Risk Configuration version: {new_version}")

            return RiskConfigurationResponse(
                config_version=new_version,
                weights=weights,
                thresholds=thresholds,
                night_start_time=night_start,
                night_end_time=night_end,
                enabled_factors=enabled,
                is_active=True,
                created_at=now_dt.isoformat(),
                updated_at=now_dt.isoformat()
            )
        finally:
            db.close()

    def get_risk_summary(self) -> RiskSummaryResponse:
        """Computes system-wide risk statistics and camera sector risk distribution."""
        db = SessionLocal()
        try:
            assessments = db.query(RiskAssessmentModel).all()
            total = len(assessments)
            
            low = sum(1 for a in assessments if a.risk_level == "LOW")
            med = sum(1 for a in assessments if a.risk_level == "MEDIUM")
            high = sum(1 for a in assessments if a.risk_level in ("HIGH", "CRITICAL"))
            avg_score = round(sum(a.score for a in assessments) / max(1, total), 1)

            active_cfg = db.query(RiskConfigurationModel).filter(RiskConfigurationModel.is_active == True).first()
            cfg_ver = active_cfg.config_version if active_cfg else "v1.0.0"

            # Compute camera risk levels based on incidents on each camera
            cameras = db.query(CameraModel).all()
            cam_risk: Dict[str, str] = {}

            for cam in cameras:
                # Find all subjects who visited this camera
                subject_links = db.query(SubjectTrackLinkModel.subject_id).filter(
                    SubjectTrackLinkModel.camera_id == cam.camera_id
                ).distinct().all()
                s_ids = [s[0] for s in subject_links]

                if not s_ids:
                    cam_risk[cam.camera_id] = "LOW"
                    continue

                # Find max risk level for incidents of these subjects
                incidents = db.query(IncidentModel).filter(IncidentModel.subject_id.in_(s_ids)).all()
                inc_ids = [i.incident_id for i in incidents]

                cam_assessments = db.query(RiskAssessmentModel).filter(
                    RiskAssessmentModel.incident_id.in_(inc_ids)
                ).all()

                if any(a.risk_level in ("HIGH", "CRITICAL") for a in cam_assessments):
                    cam_risk[cam.camera_id] = "HIGH"
                elif any(a.risk_level == "MEDIUM" for a in cam_assessments):
                    cam_risk[cam.camera_id] = "MEDIUM"
                else:
                    cam_risk[cam.camera_id] = "LOW"

            return RiskSummaryResponse(
                total_incidents_assessed=total,
                low_risk_count=low,
                medium_risk_count=med,
                high_risk_count=high,
                average_risk_score=avg_score,
                active_config_version=cfg_ver,
                camera_risk_distribution=cam_risk
            )
        finally:
            db.close()

    def get_incident_intelligence(self, incident_id: str) -> Optional[IncidentIntelligenceResponse]:
        """
        Builds the standardized Phase 6 Intelligence Object for downstream Command & Response.
        """
        db = SessionLocal()
        try:
            inc = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
            if not inc:
                return None

            risk_resp = self.get_incident_risk(incident_id)
            if not risk_resp:
                return None

            # Get timeline
            event_links = db.query(IncidentEventLinkModel).filter(
                IncidentEventLinkModel.incident_id == incident_id
            ).order_by(IncidentEventLinkModel.sequence_number.asc()).all()
            event_ids = [l.event_id for l in event_links]

            events = db.query(SecurityEventModel).filter(
                SecurityEventModel.event_id.in_(event_ids)
            ).all() if event_ids else []

            timeline = [
                {
                    "event_id": e.event_id,
                    "camera_id": e.camera_id,
                    "event_type": e.event_type,
                    "zone_name": e.zone_name,
                    "confidence": e.confidence,
                    "timestamp": e.created_at.isoformat()
                }
                for e in events
            ]

            # Get journey
            journey_links = db.query(SubjectTrackLinkModel).filter(
                SubjectTrackLinkModel.subject_id == inc.subject_id
            ).order_by(SubjectTrackLinkModel.first_timestamp.asc()).all()

            journey = [
                {
                    "camera_id": j.camera_id,
                    "track_id": j.track_id,
                    "formatted_track_id": j.formatted_track_id,
                    "match_score": j.match_score,
                    "match_status": j.match_status,
                    "first_timestamp": j.first_timestamp.isoformat(),
                    "last_timestamp": j.last_timestamp.isoformat()
                }
                for j in journey_links
            ]

            # Get context
            cams = list(set([j.camera_id for j in journey_links] + [e.camera_id for e in events]))
            zones = list(set([e.zone_name for e in events if e.zone_name]))
            
            vehicles_orm = db.query(AssociatedVehicleModel).filter(
                AssociatedVehicleModel.subject_id == inc.subject_id
            ).all()
            vehicles = [v.vehicle_subject_id for v in vehicles_orm]

            factors_list = [
                {
                    "type": f.factor_type,
                    "name": f.factor_name,
                    "contribution": f.contribution,
                    "evidence": f.evidence,
                    "confidence": f.confidence
                }
                for f in risk_resp.factors if f.is_available and f.contribution > 0
            ]

            return IncidentIntelligenceResponse(
                incident_id=incident_id,
                subject_id=inc.subject_id,
                risk={
                    "score": risk_resp.score,
                    "level": risk_resp.risk_level,
                    "confidence": risk_resp.confidence,
                    "config_version": risk_resp.config_version
                },
                factors=factors_list,
                explanation=risk_resp.explanation,
                context={
                    "cameras": cams,
                    "zones": zones,
                    "events": event_ids,
                    "vehicles": vehicles
                },
                timeline=timeline,
                journey=journey,
                updated_at=risk_resp.updated_at
            )
        finally:
            db.close()


risk_service = RiskService()
