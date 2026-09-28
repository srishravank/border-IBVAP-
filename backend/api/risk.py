import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.models.risk import (
    RiskAssessmentResponse,
    RiskFactorResponse,
    RiskHistoryResponse,
    RiskConfigurationResponse,
    UpdateRiskConfigurationPayload,
    RiskSummaryResponse,
    IncidentIntelligenceResponse
)
from backend.services.risk_service import risk_service

logger = logging.getLogger("ibvap.api.risk")

router = APIRouter(prefix="/api", tags=["Intelligence & Explainable Risk Engine (Phase 5)"])


@router.get(
    "/incidents/{incident_id}/risk",
    response_model=RiskAssessmentResponse,
    summary="Get Explainable Risk Assessment for an Incident"
)
async def get_incident_risk(incident_id: str, recalculate: bool = Query(False, description="Force re-evaluation")):
    """
    Returns the latest explainable multi-factor risk assessment for a specific incident.
    Every factor details its exact contribution points, evidence, and confidence rating.
    """
    assessment = risk_service.evaluate_incident(incident_id, force=recalculate) if recalculate else risk_service.get_incident_risk(incident_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found or risk assessment could not be generated."
        )
    return assessment


@router.get(
    "/incidents/{incident_id}/risk/history",
    response_model=List[RiskHistoryResponse],
    summary="Get Chronological Risk History for an Incident"
)
async def get_incident_risk_history(incident_id: str):
    """
    Returns the chronological progression of risk scores and factor updates as new evidence was verified.
    """
    return risk_service.get_incident_risk_history(incident_id)


@router.get(
    "/incidents/{incident_id}/risk/factors",
    response_model=List[RiskFactorResponse],
    summary="Get Contributing Risk Factors for an Incident"
)
async def get_incident_risk_factors(incident_id: str):
    """
    Returns the granular breakdown of all contributing factors and traceable source event IDs.
    """
    assessment = risk_service.get_incident_risk(incident_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found."
        )
    return assessment.factors


@router.get(
    "/risk/config",
    response_model=RiskConfigurationResponse,
    summary="Get Active Risk Engine Configuration"
)
async def get_risk_config():
    """
    Returns the currently active weights, thresholds, night window, and enabled factor list.
    """
    return risk_service.get_active_config()


@router.put(
    "/risk/config",
    response_model=RiskConfigurationResponse,
    summary="Update Risk Engine Configuration (Creates New Version)"
)
async def update_risk_config(payload: UpdateRiskConfigurationPayload):
    """
    Updates the risk engine weights, thresholds, night window, or enabled factors.
    Creates a new versioned preset for full traceability.
    """
    try:
        return risk_service.update_config(payload)
    except Exception as e:
        logger.error(f"Error updating risk config: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update risk configuration: {str(e)}"
        )


@router.get(
    "/risk/summary",
    response_model=RiskSummaryResponse,
    summary="Get System-Wide Risk Overview"
)
async def get_risk_summary():
    """
    Returns high-level statistics on assessed incidents, risk level distributions, and camera risk levels.
    """
    return risk_service.get_risk_summary()


@router.get(
    "/incidents/{incident_id}/intelligence",
    response_model=IncidentIntelligenceResponse,
    summary="Get Phase 6 Standardized Intelligence Object"
)
async def get_incident_intelligence(incident_id: str):
    """
    Returns the unified, structured intelligence object consumed by Phase 6 Command & Response.
    """
    intel = risk_service.get_incident_intelligence(incident_id)
    if not intel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found."
        )
    return intel
