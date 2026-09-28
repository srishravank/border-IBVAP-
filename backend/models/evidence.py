from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class EvidenceInclusionSummary(BaseModel):
    incident_metadata: bool = True
    verified_events_count: int = 0
    cameras_involved_count: int = 0
    subject_journey_included: bool = True
    risk_assessment_included: bool = True
    operator_actions_count: int = 0
    operator_notes_count: int = 0
    media_references_count: int = 0


class EvidenceManifest(BaseModel):
    """Deterministic, canonical representation of all relevant Phase 1–6 evidence."""
    schema_version: str = "1.0"
    evidence_package_id: str
    incident_id: str
    version: str = "1.0"
    generated_at: str

    incident: Dict[str, Any]
    events: List[Dict[str, Any]]
    journey: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    operator_actions: List[Dict[str, Any]]
    operator_notes: List[Dict[str, Any]]
    status_history: List[Dict[str, Any]]
    media_references: List[Dict[str, Any]]


class GenerateEvidenceRequest(BaseModel):
    operator_id: str = "OP-9402"
    role: str = "OPERATOR"
    version: str = "1.0"
    notes: Optional[str] = None


class VerifyEvidenceRequest(BaseModel):
    operator_id: str = "OP-9402"
    role: str = "OPERATOR"


class TamperDemoRequest(BaseModel):
    tamper_field: str = "risk_score"  # "risk_score", "timestamp", "event_type", "camera_id"
    tamper_value: Optional[Any] = None


class LedgerAnchorResponse(BaseModel):
    transaction_id: str
    evidence_id: str
    incident_id: str
    version: str
    block_number: int
    block_hash: str
    previous_block_hash: str
    anchored_hash: str
    ledger_type: str
    timestamp: str
    status: str


class EvidenceHashResponse(BaseModel):
    evidence_id: str
    algorithm: str = "SHA-256"
    hash_value: str
    canonical_size_bytes: int
    created_at: str


class EvidenceVerificationResponse(BaseModel):
    verification_id: str
    evidence_id: str
    incident_id: str
    status: str  # AUTHENTIC, TAMPERED, NOT_FOUND
    is_authentic: bool
    calculated_hash: str
    anchored_hash: str
    algorithm: str = "SHA-256"
    verified_at: str
    verified_by: str
    role: str
    details: Dict[str, Any] = Field(default_factory=dict)
    tamper_analysis: Optional[str] = None


class EvidenceAuditLogResponse(BaseModel):
    log_id: str
    evidence_id: str
    incident_id: str
    action: str
    operator_id: str
    role: str
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidencePackageResponse(BaseModel):
    evidence_id: str
    incident_id: str
    version: str
    status: str  # CREATED, ANCHORED, ANCHOR_PENDING, TAMPERED
    storage_path: str
    manifest_path: str
    created_at: str
    created_by: str
    role: str
    hash: EvidenceHashResponse
    anchor: Optional[LedgerAnchorResponse] = None
    latest_verification: Optional[EvidenceVerificationResponse] = None
    inclusion_summary: EvidenceInclusionSummary
