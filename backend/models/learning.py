from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# --- Model Registry Schemas ---

class ModelVersionResponse(BaseModel):
    model_id: str
    version: str
    parent_version: Optional[str] = None
    model_type: str = "YOLOv9"
    model_hash: str
    training_round: int = 0
    status: str  # ACTIVE, CANDIDATE, ARCHIVED, REJECTED
    validation_status: str  # PENDING, VALIDATED, APPROVED, REJECTED
    metrics: Dict[str, Any] = Field(default_factory=dict)
    model_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_by: str
    created_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None


class ModelComparisonMetric(BaseModel):
    metric_name: str
    active_value: float
    candidate_value: float
    diff: float
    improved: bool


class ModelValidationResponse(BaseModel):
    candidate_model_id: str
    candidate_version: str
    active_model_id: str
    active_version: str
    validation_status: str  # PASS, FAIL, REVIEW_REQUIRED
    metrics_comparison: List[ModelComparisonMetric]
    overall_mAP: float
    precision: float
    recall: float
    f1_score: float
    evaluated_samples: int
    evaluated_at: datetime
    recommendation: str


# --- Training Sample Schemas ---

class TrainingSampleResponse(BaseModel):
    sample_id: str
    edge_id: str
    camera_id: str
    source_event_id: Optional[str] = None
    label: str
    label_source: str  # AUTO_COLLECTED, OPERATOR_REVIEWED, VALIDATED, REJECTED
    validation_status: str  # PENDING, VALIDATED, REJECTED
    confidence: float
    bbox: List[float] = Field(default_factory=list)
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    sample_metadata: Dict[str, Any] = Field(default_factory=dict)


class SampleReviewRequest(BaseModel):
    action: str = Field(..., description="APPROVE, REJECT, RELABEL")
    corrected_label: Optional[str] = None
    operator_id: str = "OP-9402"
    role: str = "OPERATOR"
    notes: Optional[str] = None


# --- Local Training Schemas ---

class LocalTrainingStartRequest(BaseModel):
    epochs: int = Field(5, ge=1, le=50)
    batch_size: int = Field(16, ge=1, le=128)
    learning_rate: float = Field(0.001, gt=0.0)
    device: Optional[str] = None
    simulation_mode: bool = False
    operator_id: str = "OP-9402"
    role: str = "ADMIN"


class TrainingRunResponse(BaseModel):
    run_id: str
    edge_id: str
    base_model_version: str
    sample_count: int
    epochs: int
    batch_size: int
    learning_rate: float
    status: str  # RUNNING, COMPLETED, FAILED, CANCELLED
    training_loss: float
    validation_metric: float
    metrics: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class LocalTrainingStatusResponse(BaseModel):
    edge_id: str
    is_training: bool
    active_model_version: str
    validated_samples_available: int
    minimum_samples_required: int
    ready_for_training: bool
    current_run: Optional[TrainingRunResponse] = None
    last_completed_run: Optional[TrainingRunResponse] = None
    training_device: str
    resource_policy: Dict[str, Any] = Field(default_factory=dict)


# --- Model Update Schemas ---

class ModelUpdateResponse(BaseModel):
    update_id: str
    edge_id: str
    base_model_version: str
    training_round: int
    sample_count: int
    training_loss: float
    validation_metric: float
    update_hash: str
    status: str  # CREATED, QUEUED, SUBMITTED, REJECTED, AGGREGATED
    created_at: datetime
    metrics: Dict[str, Any] = Field(default_factory=dict)


# --- Federated Round Schemas ---

class FederatedRoundResponse(BaseModel):
    round_id: str
    base_model_version: str
    participants: List[str] = Field(default_factory=list)
    updates_received: int
    aggregation_method: str = "FEDAVG"
    candidate_model_id: Optional[str] = None
    status: str  # OPEN, COLLECTING, AGGREGATING, COMPLETED, FAILED
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class CreateFederatedRoundRequest(BaseModel):
    base_model_version: Optional[str] = None
    participating_edges: List[str] = Field(default_factory=lambda: ["EDGE-SECTOR-A-01", "EDGE-SECTOR-A-02", "EDGE-SECTOR-B-01"])
    aggregation_method: str = "FEDAVG"
    operator_id: str = "OP-9402"
    role: str = "ADMIN"


# --- Governance Schemas ---

class ModelApprovalRequest(BaseModel):
    operator_id: str = "OP-9402"
    role: str = "SUPERVISOR"
    notes: Optional[str] = None


class ModelDeploymentRequest(BaseModel):
    operator_id: str = "OP-9402"
    role: str = "ADMIN"
    notes: Optional[str] = None


class ModelRollbackRequest(BaseModel):
    operator_id: str = "OP-9402"
    role: str = "ADMIN"
    reason: str = "Operational regression detected"


class ModelAuditLogResponse(BaseModel):
    log_id: str
    model_id: str
    action: str
    actor: str
    role: str
    timestamp: datetime
    log_metadata: Dict[str, Any] = Field(default_factory=dict)


class PrivacyStatusResponse(BaseModel):
    edge_id: str
    raw_cctv_shared: bool = False
    raw_images_shared: bool = False
    local_training_enabled: bool = True
    model_updates_shared: bool = True
    training_metrics_shared: bool = True
    cryptographic_hashes_shared: bool = True
    audit_guarantee: str = "Zero raw surveillance footage or imagery is transmitted off the edge outpost."
    last_audit_timestamp: datetime
