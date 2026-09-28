import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from backend.config import settings
from backend.database.connection import db_session_scope
from backend.database.models import TrainingSampleModel

logger = logging.getLogger("ibvap.training.samples")


class TrainingSampleService:
    """
    Service for managing edge training sample collection, provenance tracking,
    and human-in-the-loop validation triage.
    """

    def __init__(self):
        self._ensure_sample_pool()

    def collect_sample(
        self,
        camera_id: str,
        label: str,
        confidence: float,
        bbox: List[float],
        source_event_id: Optional[str] = None,
        edge_id: Optional[str] = None,
        label_source: str = "AUTO_COLLECTED",
        validation_status: str = "PENDING",
        sample_metadata: Optional[Dict[str, Any]] = None,
        reviewed_by: Optional[str] = None
    ) -> TrainingSampleModel:
        """
        Collects a new training sample candidate from camera operations.
        Defaults to PENDING status until validated by an operator.
        """
        sample_id = f"SMP-{uuid.uuid4().hex[:6].upper()}"
        edge = edge_id or settings.EDGE_ID

        with db_session_scope() as session:
            sample = TrainingSampleModel(
                sample_id=sample_id,
                edge_id=edge,
                camera_id=camera_id,
                source_event_id=source_event_id,
                label=label.lower(),
                label_source=label_source,
                validation_status=validation_status,
                confidence=round(confidence, 3),
                bbox_json=json.dumps(bbox or []),
                metadata_json=json.dumps(sample_metadata or {
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                    "environment": "Border Zone Outpost",
                    "lighting": "Daylight / Low-Light"
                }),
                reviewed_by=reviewed_by,
                reviewed_at=datetime.now(timezone.utc) if validation_status != "PENDING" else None,
                created_at=datetime.now(timezone.utc)
            )
            session.add(sample)
            session.flush()
            session.expunge(sample)
            logger.info(f"Collected training sample {sample_id} ({label}) with status {validation_status}")
            return sample

    def list_samples(
        self,
        validation_status: Optional[str] = None,
        label: Optional[str] = None,
        limit: int = 100
    ) -> List[TrainingSampleModel]:
        """Lists training samples filtered by status and label."""
        with db_session_scope() as session:
            query = session.query(TrainingSampleModel)
            if validation_status:
                query = query.filter(TrainingSampleModel.validation_status == validation_status)
            if label:
                query = query.filter(TrainingSampleModel.label == label.lower())
            samples = query.order_by(TrainingSampleModel.created_at.desc()).limit(limit).all()
            for s in samples:
                session.expunge(s)
            return samples

    get_samples = list_samples

    def get_sample(self, sample_id: str) -> Optional[TrainingSampleModel]:
        """Retrieves a single training sample by ID."""
        with db_session_scope() as session:
            sample = session.query(TrainingSampleModel).filter(
                TrainingSampleModel.sample_id == sample_id
            ).first()
            if sample:
                session.expunge(sample)
            return sample

    def get_validated_samples_count(self) -> int:
        """Returns the count of samples currently marked as VALIDATED."""
        with db_session_scope() as session:
            return session.query(TrainingSampleModel).filter(
                TrainingSampleModel.validation_status == "VALIDATED"
            ).count()

    def get_validated_samples(self) -> List[TrainingSampleModel]:
        """Retrieves all VALIDATED samples eligible for local training."""
        with db_session_scope() as session:
            samples = session.query(TrainingSampleModel).filter(
                TrainingSampleModel.validation_status == "VALIDATED"
            ).all()
            for s in samples:
                session.expunge(s)
            return samples

    def review_sample(
        self,
        sample_id: str,
        action: str,
        corrected_label: Optional[str] = None,
        operator_id: str = "OP-9402",
        role: str = "OPERATOR",
        notes: Optional[str] = None
    ) -> TrainingSampleModel:
        """
        Human-In-The-Loop review action: APPROVE, REJECT, or RELABEL.
        """
        with db_session_scope() as session:
            sample = session.query(TrainingSampleModel).filter(
                TrainingSampleModel.sample_id == sample_id
            ).first()
            if not sample:
                raise ValueError(f"Training sample '{sample_id}' not found.")

            act = action.upper()
            now = datetime.now(timezone.utc)
            meta = sample.sample_metadata or {}
            meta["review_notes"] = notes or ""
            meta["reviewer_role"] = role

            if act == "APPROVE":
                sample.validation_status = "VALIDATED"
                sample.label_source = "OPERATOR_REVIEWED"
                sample.reviewed_by = operator_id
                sample.reviewed_at = now
            elif act == "REJECT":
                sample.validation_status = "REJECTED"
                sample.label_source = "REJECTED"
                sample.reviewed_by = operator_id
                sample.reviewed_at = now
            elif act == "RELABEL":
                if not corrected_label:
                    raise ValueError("corrected_label is required when action is RELABEL.")
                meta["original_label"] = sample.label
                sample.label = corrected_label.lower()
                sample.validation_status = "VALIDATED"
                sample.label_source = "OPERATOR_REVIEWED"
                sample.reviewed_by = operator_id
                sample.reviewed_at = now
            else:
                raise ValueError(f"Unknown review action '{action}'. Use APPROVE, REJECT, or RELABEL.")

            sample.sample_metadata = meta
            session.flush()
            session.expunge(sample)
            logger.info(f"Operator {operator_id} ({role}) reviewed sample {sample_id} -> {sample.validation_status}")
            return sample

    def _ensure_sample_pool(self):
        """Initializes a rich set of training samples for immediate demonstration."""
        try:
            with db_session_scope() as session:
                count = session.query(TrainingSampleModel).count()
                if count < 10:
                    self._seed_default_samples(session)
        except Exception as e:
            logger.error(f"Error ensuring sample pool: {e}")

    def _seed_default_samples(self, session):
        """Seeds initial synthetic/demonstration samples with provenance."""
        sample_configs = [
            ("CAM-SECTOR-A1", "person", 0.92, [120, 150, 240, 480], "EVT-001", "VALIDATED", "OPERATOR_REVIEWED", "OP-9402"),
            ("CAM-SECTOR-A1", "person", 0.88, [310, 200, 410, 510], "EVT-002", "VALIDATED", "OPERATOR_REVIEWED", "OP-9402"),
            ("CAM-SECTOR-A2", "vehicle", 0.94, [400, 300, 750, 600], "EVT-003", "VALIDATED", "OPERATOR_REVIEWED", "OP-9402"),
            ("CAM-SECTOR-A2", "truck", 0.89, [200, 250, 600, 580], "EVT-004", "VALIDATED", "OPERATOR_REVIEWED", "OP-9402"),
            ("CAM-SECTOR-B1", "person", 0.78, [500, 180, 580, 420], None, "VALIDATED", "OPERATOR_REVIEWED", "OP-9402"),
            ("CAM-SECTOR-B1", "motorcycle", 0.85, [150, 220, 280, 390], None, "VALIDATED", "OPERATOR_REVIEWED", "OP-9402"),
            ("CAM-SECTOR-B2", "person", 0.91, [100, 120, 190, 410], "EVT-005", "VALIDATED", "OPERATOR_REVIEWED", "OP-9402"),
            ("CAM-SECTOR-A1", "car", 0.87, [350, 280, 620, 500], None, "VALIDATED", "OPERATOR_REVIEWED", "OP-9402"),
            ("CAM-SECTOR-A2", "person", 0.84, [220, 190, 300, 440], "EVT-006", "VALIDATED", "OPERATOR_REVIEWED", "OP-9402"),
            ("CAM-SECTOR-B2", "vehicle", 0.90, [450, 310, 780, 620], None, "VALIDATED", "OPERATOR_REVIEWED", "OP-9402"),
            ("CAM-SECTOR-A1", "person", 0.86, [180, 160, 260, 450], "EVT-007", "VALIDATED", "OPERATOR_REVIEWED", "OP-9402"),
            ("CAM-SECTOR-A2", "person", 0.89, [280, 210, 370, 490], "EVT-008", "VALIDATED", "OPERATOR_REVIEWED", "OP-9402"),
            # Pending samples for operator triage
            ("CAM-SECTOR-A1", "person", 0.61, [520, 310, 590, 490], None, "PENDING", "AUTO_COLLECTED", None),
            ("CAM-SECTOR-A2", "car", 0.68, [110, 340, 320, 490], None, "PENDING", "AUTO_COLLECTED", None),
            ("CAM-SECTOR-B1", "vehicle", 0.58, [420, 220, 610, 400], None, "PENDING", "AUTO_COLLECTED", None),
            ("CAM-SECTOR-B2", "person", 0.64, [300, 150, 380, 390], None, "PENDING", "AUTO_COLLECTED", None),
            # Rejected samples (false positives / shadows)
            ("CAM-SECTOR-B1", "person", 0.42, [50, 50, 120, 200], None, "REJECTED", "REJECTED", "OP-9402")
        ]

        for i, (cam, lbl, conf, bbox, evt_id, st, src, rev) in enumerate(sample_configs):
            s_id = f"SMP-{1000 + i}"
            existing = session.query(TrainingSampleModel).filter(TrainingSampleModel.sample_id == s_id).first()
            if existing:
                continue
            sample = TrainingSampleModel(
                sample_id=s_id,
                edge_id=settings.EDGE_ID,
                camera_id=cam,
                source_event_id=evt_id,
                label=lbl,
                label_source=src,
                validation_status=st,
                confidence=conf,
                bbox_json=json.dumps(bbox),
                metadata_json=json.dumps({"env": "Border Perimeter", "source": "Edge AI Inference"}),
                reviewed_by=rev,
                reviewed_at=datetime.now(timezone.utc) if st != "PENDING" else None,
                created_at=datetime.now(timezone.utc)
            )
            session.add(sample)
        logger.info("Seeded initial training samples pool.")


    def seed_demo_samples(self, count: int = 5):
        """Seeds demo training samples into the database."""
        with db_session_scope() as session:
            self._seed_default_samples(session)


# Global singleton Training Sample service
training_sample_service = TrainingSampleService()

