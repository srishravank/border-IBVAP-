from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class RiskFactorResponse(BaseModel):
    factor_id: str
    factor_type: str
    factor_name: str
    contribution: float
    confidence: float
    evidence: str
    source_event_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_available: bool = True


class RiskAssessmentResponse(BaseModel):
    assessment_id: str
    incident_id: str
    subject_id: str
    score: float
    risk_level: str
    confidence: float
    config_version: str
    explanation: str
    factors: List[RiskFactorResponse] = Field(default_factory=list)
    evidence_checklist: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: str


class RiskHistoryResponse(BaseModel):
    history_id: str
    incident_id: str
    assessment_id: str
    score: float
    risk_level: str
    factors_summary: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: str


class RiskConfigurationResponse(BaseModel):
    config_version: str
    weights: Dict[str, float]
    thresholds: Dict[str, float]
    night_start_time: str
    night_end_time: str
    enabled_factors: List[str]
    is_active: bool
    created_at: str
    updated_at: str


class UpdateRiskConfigurationPayload(BaseModel):
    weights: Optional[Dict[str, float]] = None
    thresholds: Optional[Dict[str, float]] = None
    night_start_time: Optional[str] = None
    night_end_time: Optional[str] = None
    enabled_factors: Optional[List[str]] = None


class RiskSummaryResponse(BaseModel):
    total_incidents_assessed: int
    low_risk_count: int
    medium_risk_count: int
    high_risk_count: int
    average_risk_score: float
    active_config_version: str
    camera_risk_distribution: Dict[str, str] = Field(default_factory=dict)


class IncidentIntelligenceResponse(BaseModel):
    """
    Standardized Intelligence Object exposed for Phase 6 Command & Response.
    """
    incident_id: str
    subject_id: str
    risk: Dict[str, Any]
    factors: List[Dict[str, Any]]
    explanation: str
    context: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    journey: List[Dict[str, Any]]
    updated_at: str
