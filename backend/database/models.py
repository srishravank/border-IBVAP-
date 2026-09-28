import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Float, Integer, Text, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class CameraModel(Base):
    """SQLAlchemy ORM model for storing CCTV camera configuration and persistent state."""
    __tablename__ = "cameras"

    camera_id = Column(String(64), primary_key=True, index=True)
    camera_name = Column(String(128), nullable=False)
    location = Column(String(128), nullable=False)
    source_type = Column(String(32), nullable=False)  # rtsp, file, webcam
    source = Column(String(512), nullable=False)       # rtsp url, file path, webcam index
    enabled = Column(Boolean, default=True, nullable=False)
    status = Column(String(32), default="OFFLINE", nullable=False)
    
    target_fps = Column(Float, default=25.0, nullable=False)
    frame_width = Column(Integer, default=1280, nullable=False)
    frame_height = Column(Integer, default=720, nullable=False)
    description = Column(Text, default="", nullable=True)
    extra_config_json = Column(Text, default="{}", nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen = Column(DateTime, nullable=True)

    @property
    def extra_config(self) -> dict:
        try:
            return json.loads(self.extra_config_json) if self.extra_config_json else {}
        except Exception:
            return {}

    @extra_config.setter
    def extra_config(self, val: dict):
        self.extra_config_json = json.dumps(val or {})


class CameraHealthEventModel(Base):
    """SQLAlchemy ORM model for tracking camera lifecycle and health diagnostic events."""
    __tablename__ = "camera_health_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_id = Column(String(64), index=True, nullable=False)
    event_type = Column(String(64), index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    frame_id = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    details_json = Column(Text, default="{}", nullable=True)

    @property
    def details(self) -> dict:
        try:
            return json.loads(self.details_json) if self.details_json else {}
        except Exception:
            return {}

    @details.setter
    def details(self, val: dict):
        self.details_json = json.dumps(val or {})


class ZoneModel(Base):
    """SQLAlchemy ORM model for storing polygon virtual fence zones."""
    __tablename__ = "zones"

    zone_id = Column(String(64), primary_key=True, index=True)
    camera_id = Column(String(64), index=True, nullable=False)
    zone_name = Column(String(128), nullable=False)
    zone_type = Column(String(32), default="restricted", nullable=False)  # restricted, exclusion, checkpoint
    polygon_json = Column(Text, nullable=False)  # [[x1, y1], [x2, y2], ...]
    enabled = Column(Boolean, default=True, nullable=False)
    sensitivity = Column(String(32), default="high", nullable=False)  # low, medium, high
    description = Column(Text, default="", nullable=True)
    color = Column(String(32), default="#F43F5E", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def polygon(self) -> list:
        try:
            return json.loads(self.polygon_json) if self.polygon_json else []
        except Exception:
            return []

    @polygon.setter
    def polygon(self, val: list):
        self.polygon_json = json.dumps(val or [])


class SecurityEventModel(Base):
    """SQLAlchemy ORM model for storing verified security incidents and candidate alerts."""
    __tablename__ = "security_events"

    event_id = Column(String(64), primary_key=True, index=True)
    camera_id = Column(String(64), index=True, nullable=False)
    track_id = Column(Integer, index=True, nullable=False)
    formatted_track_id = Column(String(32), nullable=False)
    zone_id = Column(String(64), index=True, nullable=False)
    zone_name = Column(String(128), nullable=False)
    event_type = Column(String(64), index=True, nullable=False)  # ZONE_ENTRY, ZONE_EXIT, ZONE_INTRUSION
    status = Column(String(32), index=True, default="CANDIDATE", nullable=False)  # CANDIDATE, VERIFYING, CONFIRMED, REJECTED, EXPIRED, ACKNOWLEDGED
    
    confidence = Column(Float, default=0.0, nullable=False)
    object_type = Column(String(32), nullable=False)  # person, vehicle
    class_name = Column(String(32), nullable=False)
    subclass = Column(String(32), nullable=True)
    
    bbox_json = Column(Text, default="[]", nullable=False)
    reference_point_json = Column(Text, default="[]", nullable=False)
    trajectory_json = Column(Text, default="[]", nullable=True)
    verification_json = Column(Text, default="{}", nullable=False)
    description = Column(Text, default="", nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    @property
    def bbox(self) -> list:
        try:
            return json.loads(self.bbox_json) if self.bbox_json else []
        except Exception:
            return []

    @bbox.setter
    def bbox(self, val: list):
        self.bbox_json = json.dumps(val or [])

    @property
    def reference_point(self) -> list:
        try:
            return json.loads(self.reference_point_json) if self.reference_point_json else []
        except Exception:
            return []

    @reference_point.setter
    def reference_point(self, val: list):
        self.reference_point_json = json.dumps(val or [])

    @property
    def trajectory(self) -> list:
        try:
            return json.loads(self.trajectory_json) if self.trajectory_json else []
        except Exception:
            return []

    @trajectory.setter
    def trajectory(self, val: list):
        self.trajectory_json = json.dumps(val or [])

    @property
    def verification(self) -> dict:
        try:
            return json.loads(self.verification_json) if self.verification_json else {}
        except Exception:
            return {}

    @verification.setter
    def verification(self, val: dict):
        self.verification_json = json.dumps(val or {})


class CameraTopologyModel(Base):
    """SQLAlchemy ORM model for storing inter-camera spatial transitions and temporal constraints."""
    __tablename__ = "camera_topology"

    relation_id = Column(String(64), primary_key=True, index=True)
    source_camera = Column(String(64), index=True, nullable=False)
    destination_camera = Column(String(64), index=True, nullable=False)
    min_transition_seconds = Column(Float, default=5.0, nullable=False)
    max_transition_seconds = Column(Float, default=180.0, nullable=False)
    distance_meters = Column(Float, default=50.0, nullable=False)
    direction = Column(String(32), default="bidirectional", nullable=False)  # forward, reverse, bidirectional
    enabled = Column(Boolean, default=True, nullable=False)
    description = Column(Text, default="", nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class SubjectModel(Base):
    """SQLAlchemy ORM model for storing global cross-camera subjects (e.g. SUBJ-001, VEH-001)."""
    __tablename__ = "subjects"

    subject_id = Column(String(64), primary_key=True, index=True)
    object_type = Column(String(32), default="person", nullable=False)  # person, vehicle
    status = Column(String(32), default="ACTIVE", nullable=False)        # ACTIVE, ARCHIVED
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    initial_camera_id = Column(String(64), nullable=False)
    initial_track_id = Column(Integer, nullable=False)
    total_cameras_visited = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class SubjectTrackLinkModel(Base):
    """SQLAlchemy ORM model linking a camera-local track to a global cross-camera subject."""
    __tablename__ = "subject_track_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(String(64), index=True, nullable=False)
    camera_id = Column(String(64), index=True, nullable=False)
    track_id = Column(Integer, index=True, nullable=False)
    formatted_track_id = Column(String(32), nullable=False)
    match_score = Column(Float, default=1.0, nullable=False)
    match_status = Column(String(32), default="CONFIRMED_LINK", nullable=False)  # NO_MATCH, POSSIBLE_MATCH, LIKELY_MATCH, CONFIRMED_LINK
    evidence_json = Column(Text, default="[]", nullable=False)  # List of explainable factors
    first_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    linked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def evidence(self) -> list:
        try:
            return json.loads(self.evidence_json) if self.evidence_json else []
        except Exception:
            return []

    @evidence.setter
    def evidence(self, val: list):
        self.evidence_json = json.dumps(val or [])


class IncidentModel(Base):
    """SQLAlchemy ORM model for representing a unified multi-camera cross-zone security incident."""
    __tablename__ = "incidents"

    incident_id = Column(String(64), primary_key=True, index=True)
    subject_id = Column(String(64), index=True, nullable=False)
    status = Column(String(32), default="ACTIVE", nullable=False)  # ACTIVE, REVIEWED, CLOSED
    title = Column(String(256), nullable=False)
    summary = Column(Text, default="", nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class IncidentEventLinkModel(Base):
    """SQLAlchemy ORM model mapping confirmed Phase 3 events to an Incident in sequence."""
    __tablename__ = "incident_event_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(64), index=True, nullable=False)
    event_id = Column(String(64), index=True, nullable=False)
    sequence_number = Column(Integer, default=1, nullable=False)
    linked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class AssociatedVehicleModel(Base):
    """SQLAlchemy ORM model for storing contextual person-vehicle proximity associations."""
    __tablename__ = "associated_vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(String(64), index=True, nullable=False)
    vehicle_subject_id = Column(String(64), index=True, nullable=False)
    camera_id = Column(String(64), index=True, nullable=False)
    person_track_id = Column(Integer, nullable=False)
    vehicle_track_id = Column(Integer, nullable=False)
    relationship_type = Column(String(64), default="ASSOCIATED_WITH", nullable=False)
    proximity_meters = Column(Float, default=10.0, nullable=False)
    time_delta_seconds = Column(Float, default=0.0, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    notes = Column(String(256), default="Spatially and temporally associated activity", nullable=False)


class RiskAssessmentModel(Base):
    """SQLAlchemy ORM model for storing current explainable risk assessments for an incident."""
    __tablename__ = "risk_assessments"

    assessment_id = Column(String(64), primary_key=True, index=True)
    incident_id = Column(String(64), index=True, nullable=False)
    subject_id = Column(String(64), index=True, nullable=False)
    score = Column(Float, default=0.0, nullable=False)
    risk_level = Column(String(32), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    confidence = Column(Float, default=1.0, nullable=False)
    config_version = Column(String(32), default="v1.0.0", nullable=False)
    explanation = Column(Text, default="", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class RiskFactorModel(Base):
    """SQLAlchemy ORM model for recording contributing factors for an assessment."""
    __tablename__ = "risk_factors"

    factor_id = Column(String(64), primary_key=True, index=True)
    assessment_id = Column(String(64), index=True, nullable=False)
    factor_type = Column(String(64), index=True, nullable=False)
    contribution = Column(Float, default=0.0, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    evidence = Column(Text, default="", nullable=False)
    source_event_ids_json = Column(Text, default="[]", nullable=False)
    metadata_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def source_event_ids(self) -> list:
        try:
            return json.loads(self.source_event_ids_json) if self.source_event_ids_json else []
        except Exception:
            return []

    @source_event_ids.setter
    def source_event_ids(self, val: list):
        self.source_event_ids_json = json.dumps(val or [])

    @property
    def factor_metadata(self) -> dict:
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}

    @factor_metadata.setter
    def factor_metadata(self, val: dict):
        self.metadata_json = json.dumps(val or {})


class RiskHistoryModel(Base):
    """SQLAlchemy ORM model for preserving chronological risk progression of an incident."""
    __tablename__ = "risk_history"

    history_id = Column(String(64), primary_key=True, index=True)
    incident_id = Column(String(64), index=True, nullable=False)
    assessment_id = Column(String(64), index=True, nullable=False)
    score = Column(Float, default=0.0, nullable=False)
    risk_level = Column(String(32), default="LOW", nullable=False)
    factors_summary_json = Column(Text, default="[]", nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def factors_summary(self) -> list:
        try:
            return json.loads(self.factors_summary_json) if self.factors_summary_json else []
        except Exception:
            return []

    @factors_summary.setter
    def factors_summary(self, val: list):
        self.factors_summary_json = json.dumps(val or [])


class RiskConfigurationModel(Base):
    """SQLAlchemy ORM model for storing versioned risk weights, thresholds, and parameters."""
    __tablename__ = "risk_configurations"

    config_version = Column(String(32), primary_key=True, index=True)
    weights_json = Column(Text, nullable=False)
    thresholds_json = Column(Text, nullable=False)
    night_start_time = Column(String(16), default="20:00", nullable=False)
    night_end_time = Column(String(16), default="05:00", nullable=False)
    enabled_factors_json = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def weights(self) -> dict:
        try:
            return json.loads(self.weights_json) if self.weights_json else {}
        except Exception:
            return {}

    @weights.setter
    def weights(self, val: dict):
        self.weights_json = json.dumps(val or {})

    @property
    def thresholds(self) -> dict:
        try:
            return json.loads(self.thresholds_json) if self.thresholds_json else {}
        except Exception:
            return {}

    @thresholds.setter
    def thresholds(self, val: dict):
        self.thresholds_json = json.dumps(val or {})

    @property
    def enabled_factors(self) -> list:
        try:
            return json.loads(self.enabled_factors_json) if self.enabled_factors_json else []
        except Exception:
            return []

    @enabled_factors.setter
    def enabled_factors(self, val: list):
        self.enabled_factors_json = json.dumps(val or [])


class OperatorActionModel(Base):
    """SQLAlchemy ORM model for persisting operator lifecycle actions (Phase 6 & 7 audit trail)."""
    __tablename__ = "operator_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(String(64), unique=True, index=True, nullable=False)
    incident_id = Column(String(64), index=True, nullable=False)
    operator_id = Column(String(64), default="OP-001", nullable=False)
    role = Column(String(32), default="OPERATOR", nullable=False)  # OPERATOR, SUPERVISOR, INVESTIGATOR, ADMIN
    action = Column(String(64), nullable=False)  # ACKNOWLEDGE, INVESTIGATE, CLOSE, ADD_NOTE, FOCUS_CAMERA
    notes = Column(Text, default="", nullable=True)
    metadata_json = Column(Text, default="{}", nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def action_metadata(self) -> dict:
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}

    @action_metadata.setter
    def action_metadata(self, val: dict):
        self.metadata_json = json.dumps(val or {})


class IncidentNoteModel(Base):
    """SQLAlchemy ORM model for storing operator investigation notes."""
    __tablename__ = "incident_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(String(64), unique=True, index=True, nullable=False)
    incident_id = Column(String(64), index=True, nullable=False)
    operator_id = Column(String(64), default="OP-001", nullable=False)
    role = Column(String(32), default="OPERATOR", nullable=False)
    note = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class IncidentStatusHistoryModel(Base):
    """SQLAlchemy ORM model for tracking lifecycle transitions of an incident."""
    __tablename__ = "incident_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(64), index=True, nullable=False)
    previous_status = Column(String(32), nullable=False)
    new_status = Column(String(32), nullable=False)
    changed_by = Column(String(64), default="OP-001", nullable=False)
    role = Column(String(32), default="OPERATOR", nullable=False)
    notes = Column(Text, default="", nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


# --- Phase 7: Evidence Trust, Integrity & Blockchain Anchoring Models ---

class EvidencePackageModel(Base):
    """SQLAlchemy ORM model for storing metadata and off-chain file references for an incident evidence package."""
    __tablename__ = "evidence_packages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evidence_id = Column(String(64), unique=True, index=True, nullable=False)
    incident_id = Column(String(64), index=True, nullable=False)
    version = Column(String(16), default="1.0", nullable=False)
    storage_path = Column(String(512), nullable=False)
    manifest_path = Column(String(512), nullable=False)
    status = Column(String(32), default="CREATED", nullable=False)  # CREATED, ANCHORED, ANCHOR_PENDING, TAMPERED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(String(64), default="OP-9402", nullable=False)
    role = Column(String(32), default="OPERATOR", nullable=False)


class EvidenceHashModel(Base):
    """SQLAlchemy ORM model for storing the SHA-256 digest of canonical evidence manifests."""
    __tablename__ = "evidence_hashes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evidence_id = Column(String(64), unique=True, index=True, nullable=False)
    incident_id = Column(String(64), index=True, nullable=False)
    version = Column(String(16), default="1.0", nullable=False)
    algorithm = Column(String(32), default="SHA-256", nullable=False)
    hash_value = Column(String(128), nullable=False)
    canonical_size_bytes = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class LedgerAnchorModel(Base):
    """SQLAlchemy ORM model for persisting lightweight private ledger blockchain transactions."""
    __tablename__ = "ledger_anchors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(64), unique=True, index=True, nullable=False)  # TX-0001
    evidence_id = Column(String(64), index=True, nullable=False)
    incident_id = Column(String(64), index=True, nullable=False)
    version = Column(String(16), default="1.0", nullable=False)
    block_number = Column(Integer, default=1, nullable=False)
    block_hash = Column(String(128), nullable=False)
    previous_block_hash = Column(String(128), default="0"*64, nullable=False)
    anchored_hash = Column(String(128), nullable=False)
    ledger_type = Column(String(64), default="PRIVATE_IMMUTABLE_LEDGER", nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(String(32), default="CONFIRMED", nullable=False)  # CONFIRMED, PENDING


class EvidenceVerificationModel(Base):
    """SQLAlchemy ORM model for logging evidence integrity verification results."""
    __tablename__ = "evidence_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    verification_id = Column(String(64), unique=True, index=True, nullable=False)
    evidence_id = Column(String(64), index=True, nullable=False)
    incident_id = Column(String(64), index=True, nullable=False)
    calculated_hash = Column(String(128), nullable=False)
    anchored_hash = Column(String(128), nullable=False)
    result = Column(String(32), nullable=False)  # AUTHENTIC, TAMPERED, NOT_FOUND
    algorithm = Column(String(32), default="SHA-256", nullable=False)
    verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    verified_by = Column(String(64), default="OP-9402", nullable=False)
    role = Column(String(32), default="OPERATOR", nullable=False)
    details_json = Column(Text, default="{}", nullable=False)

    @property
    def details(self) -> dict:
        try:
            return json.loads(self.details_json) if self.details_json else {}
        except Exception:
            return {}

    @details.setter
    def details(self, val: dict):
        self.details_json = json.dumps(val or {})


class EvidenceAuditLogModel(Base):
    """SQLAlchemy ORM model for logging all evidence trust operations."""
    __tablename__ = "evidence_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(64), unique=True, index=True, nullable=False)
    evidence_id = Column(String(64), index=True, nullable=False)
    incident_id = Column(String(64), index=True, nullable=False)
    action = Column(String(64), nullable=False)  # EVIDENCE_CREATED, EVIDENCE_HASHED, EVIDENCE_ANCHORED, EVIDENCE_VERIFIED, EVIDENCE_TAMPERED_FOR_DEMO, EVIDENCE_RESTORED
    operator_id = Column(String(64), default="OP-9402", nullable=False)
    role = Column(String(32), default="OPERATOR", nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    metadata_json = Column(Text, default="{}", nullable=False)

    @property
    def log_metadata(self) -> dict:
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}

    @log_metadata.setter
    def log_metadata(self, val: dict):
        self.metadata_json = json.dumps(val or {})


# --- Phase 8: Offline-First Operation & Resilient Synchronization Models ---

class ConnectivityStateModel(Base):
    """SQLAlchemy ORM model for persisting connection state transitions and simulation overrides."""
    __tablename__ = "connectivity_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(String(32), default="ONLINE", nullable=False)  # ONLINE, DEGRADED, OFFLINE, RECONNECTING, SYNCING
    is_simulated = Column(Boolean, default=False, nullable=False)
    reason = Column(String(256), default="Normal connectivity", nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class SyncQueueItemModel(Base):
    """SQLAlchemy ORM model for storing durable, priority-ordered offline synchronization items."""
    __tablename__ = "sync_queue_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    edge_id = Column(String(64), default="EDGE-SECTOR-A-01", index=True, nullable=False)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)
    entity_type = Column(String(64), index=True, nullable=False)  # INCIDENT, EVENT, RISK_ASSESSMENT, EVIDENCE_PACKAGE, OPERATOR_ACTION, INCIDENT_NOTE, STATUS_TRANSITION
    entity_id = Column(String(64), index=True, nullable=False)
    operation = Column(String(32), default="CREATE", nullable=False)  # CREATE, UPDATE, ANCHOR, STATUS_CHANGE
    priority = Column(Integer, default=2, index=True, nullable=False)  # 1: CRITICAL/HIGH, 2: MEDIUM, 3: LOW
    status = Column(String(32), default="PENDING", index=True, nullable=False)  # PENDING, SYNCING, SYNCED, FAILED, RETRY_PENDING
    payload_json = Column(Text, default="{}", nullable=False)
    
    attempt_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_attempt_at = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)
    synced_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    @property
    def payload(self) -> dict:
        try:
            return json.loads(self.payload_json) if self.payload_json else {}
        except Exception:
            return {}

    @payload.setter
    def payload(self, val: dict):
        self.payload_json = json.dumps(val or {})


class SyncHistoryModel(Base):
    """SQLAlchemy ORM model for recording historical batch synchronization execution metrics."""
    __tablename__ = "sync_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_id = Column(String(64), unique=True, index=True, nullable=False)
    edge_id = Column(String(64), default="EDGE-SECTOR-A-01", nullable=False)
    status = Column(String(32), default="SUCCESS", nullable=False)  # SUCCESS, PARTIAL, FAILED
    items_synced = Column(Integer, default=0, nullable=False)
    items_failed = Column(Integer, default=0, nullable=False)
    duration_ms = Column(Float, default=0.0, nullable=False)
    error_summary = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


# --- Phase 9: On-Device / Federated Learning Models ---

class TrainingSampleModel(Base):
    """SQLAlchemy ORM model for tracking collected training samples and human-in-the-loop validation provenance."""
    __tablename__ = "training_samples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_id = Column(String(64), unique=True, index=True, nullable=False)
    edge_id = Column(String(64), default="EDGE-SECTOR-A-01", index=True, nullable=False)
    camera_id = Column(String(64), index=True, nullable=False)
    source_event_id = Column(String(64), nullable=True)
    
    label = Column(String(64), nullable=False)  # person, car, truck, motorcycle, etc.
    label_source = Column(String(32), default="AUTO_COLLECTED", nullable=False)  # AUTO_COLLECTED, OPERATOR_REVIEWED, VALIDATED, REJECTED
    validation_status = Column(String(32), default="PENDING", index=True, nullable=False)  # PENDING, VALIDATED, REJECTED
    
    confidence = Column(Float, default=0.0, nullable=False)
    bbox_json = Column(Text, default="[]", nullable=False)
    image_features_json = Column(Text, default="{}", nullable=True)
    metadata_json = Column(Text, default="{}", nullable=False)
    
    reviewed_by = Column(String(64), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def bbox(self) -> list:
        try:
            return json.loads(self.bbox_json) if self.bbox_json else []
        except Exception:
            return []

    @bbox.setter
    def bbox(self, val: list):
        self.bbox_json = json.dumps(val or [])

    @property
    def sample_metadata(self) -> dict:
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}

    @sample_metadata.setter
    def sample_metadata(self, val: dict):
        self.metadata_json = json.dumps(val or {})


class TrainingRunModel(Base):
    """SQLAlchemy ORM model for logging local edge on-device training runs."""
    __tablename__ = "training_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), unique=True, index=True, nullable=False)
    edge_id = Column(String(64), default="EDGE-SECTOR-A-01", nullable=False)
    base_model_version = Column(String(32), nullable=False)
    
    sample_count = Column(Integer, default=0, nullable=False)
    epochs = Column(Integer, default=5, nullable=False)
    batch_size = Column(Integer, default=16, nullable=False)
    learning_rate = Column(Float, default=0.001, nullable=False)
    
    status = Column(String(32), default="RUNNING", index=True, nullable=False)  # RUNNING, COMPLETED, FAILED, CANCELLED
    training_loss = Column(Float, default=0.0, nullable=False)
    validation_metric = Column(Float, default=0.0, nullable=False)
    metrics_json = Column(Text, default="{}", nullable=False)
    error_message = Column(Text, nullable=True)
    
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    @property
    def metrics(self) -> dict:
        try:
            return json.loads(self.metrics_json) if self.metrics_json else {}
        except Exception:
            return {}

    @metrics.setter
    def metrics(self, val: dict):
        self.metrics_json = json.dumps(val or {})


class ModelUpdateModel(Base):
    """SQLAlchemy ORM model for storing generated edge parameter deltas and weights updates."""
    __tablename__ = "model_updates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    update_id = Column(String(64), unique=True, index=True, nullable=False)
    edge_id = Column(String(64), default="EDGE-SECTOR-A-01", index=True, nullable=False)
    base_model_version = Column(String(32), nullable=False)
    training_round = Column(Integer, default=1, nullable=False)
    
    sample_count = Column(Integer, default=0, nullable=False)
    training_loss = Column(Float, default=0.0, nullable=False)
    validation_metric = Column(Float, default=0.0, nullable=False)
    
    weights_delta_json = Column(Text, default="{}", nullable=False)
    metrics_json = Column(Text, default="{}", nullable=False)
    update_hash = Column(String(128), nullable=False)  # SHA-256 of the update
    
    status = Column(String(32), default="CREATED", index=True, nullable=False)  # CREATED, QUEUED, SUBMITTED, REJECTED, AGGREGATED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def weights_delta(self) -> dict:
        try:
            return json.loads(self.weights_delta_json) if self.weights_delta_json else {}
        except Exception:
            return {}

    @weights_delta.setter
    def weights_delta(self, val: dict):
        self.weights_delta_json = json.dumps(val or {})

    @property
    def metrics(self) -> dict:
        try:
            return json.loads(self.metrics_json) if self.metrics_json else {}
        except Exception:
            return {}

    @metrics.setter
    def metrics(self, val: dict):
        self.metrics_json = json.dumps(val or {})


class FederatedRoundModel(Base):
    """SQLAlchemy ORM model for orchestrating federated learning aggregation rounds."""
    __tablename__ = "federated_rounds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    round_id = Column(String(64), unique=True, index=True, nullable=False)  # ROUND-001
    base_model_version = Column(String(32), nullable=False)
    
    participants_json = Column(Text, default="[]", nullable=False)
    updates_received = Column(Integer, default=0, nullable=False)
    aggregation_method = Column(String(32), default="FEDAVG", nullable=False)
    candidate_model_id = Column(String(64), nullable=True)
    
    status = Column(String(32), default="OPEN", index=True, nullable=False)  # OPEN, COLLECTING, AGGREGATING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    @property
    def participants(self) -> list:
        try:
            return json.loads(self.participants_json) if self.participants_json else []
        except Exception:
            return []

    @participants.setter
    def participants(self, val: list):
        self.participants_json = json.dumps(val or [])


class ModelVersionModel(Base):
    """SQLAlchemy ORM model for storing the global model registry and lifecycle state."""
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String(64), unique=True, index=True, nullable=False)  # e.g. MODEL-YOLO-V1.0.0
    version = Column(String(32), index=True, nullable=False)               # 1.0.0, 1.1.0
    parent_version = Column(String(32), nullable=True)
    model_type = Column(String(32), default="YOLOv9", nullable=False)
    
    model_hash = Column(String(128), nullable=False)  # SHA-256 integrity hash
    training_round = Column(Integer, default=0, nullable=False)
    
    status = Column(String(32), default="CANDIDATE", index=True, nullable=False)  # ACTIVE, CANDIDATE, ARCHIVED, REJECTED
    validation_status = Column(String(32), default="PENDING", nullable=False)      # PENDING, VALIDATED, APPROVED, REJECTED
    
    metrics_json = Column(Text, default="{}", nullable=False)
    metadata_json = Column(Text, default="{}", nullable=False)
    
    created_by = Column(String(64), default="FEDERATED_AGGREGATOR", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    approved_by = Column(String(64), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, nullable=True)

    @property
    def metrics(self) -> dict:
        try:
            return json.loads(self.metrics_json) if self.metrics_json else {}
        except Exception:
            return {}

    @metrics.setter
    def metrics(self, val: dict):
        self.metrics_json = json.dumps(val or {})

    @property
    def model_metadata(self) -> dict:
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}

    @model_metadata.setter
    def model_metadata(self, val: dict):
        self.metadata_json = json.dumps(val or {})


class ModelAuditLogModel(Base):
    """SQLAlchemy ORM model for recording immutable governance and lifecycle audit logs."""
    __tablename__ = "model_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(64), unique=True, index=True, nullable=False)
    model_id = Column(String(64), index=True, nullable=False)
    action = Column(String(64), nullable=False)  # MODEL_CREATED, LOCAL_TRAINING_STARTED, etc.
    actor = Column(String(64), default="OP-9402", nullable=False)
    role = Column(String(32), default="OPERATOR", nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    metadata_json = Column(Text, default="{}", nullable=False)

    @property
    def log_metadata(self) -> dict:
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}

    @log_metadata.setter
    def log_metadata(self, val: dict):
        self.metadata_json = json.dumps(val or {})




