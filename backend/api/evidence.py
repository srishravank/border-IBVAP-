from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Dict, Any, Optional

from backend.models.evidence import (
    EvidencePackageResponse,
    GenerateEvidenceRequest,
    VerifyEvidenceRequest,
    EvidenceVerificationResponse,
    LedgerAnchorResponse,
    EvidenceAuditLogResponse,
    TamperDemoRequest
)
from backend.services.evidence_service import evidence_service
from backend.services.ledger_service import ledger_service

evidence_router = APIRouter(tags=["Evidence Trust & Blockchain Anchoring"])


@evidence_router.get("/incidents/{incident_id}/evidence", response_model=List[EvidencePackageResponse])
def get_incident_evidence_packages(incident_id: str):
    """Retrieves all evidence package versions generated for an incident."""
    return evidence_service.get_evidence_packages(incident_id)


@evidence_router.post("/incidents/{incident_id}/evidence", response_model=EvidencePackageResponse, status_code=status.HTTP_201_CREATED)
def generate_and_anchor_evidence(incident_id: str, payload: Optional[GenerateEvidenceRequest] = None):
    """
    Compiles structured incident data from Phases 1–6 into a deterministic canonical manifest,
    calculates the SHA-256 hash, stores off-chain, and anchors the hash to the private ledger.
    """
    req = payload or GenerateEvidenceRequest()
    try:
        return evidence_service.create_and_anchor_evidence(
            incident_id=incident_id,
            operator_id=req.operator_id,
            role=req.role,
            version=req.version,
            notes=req.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@evidence_router.get("/evidence/{evidence_id}", response_model=EvidencePackageResponse)
def get_evidence_package(evidence_id: str):
    """Retrieves detailed evidence package metadata by evidence package ID."""
    pkg = evidence_service.get_evidence_package(evidence_id)
    if not pkg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evidence package {evidence_id} not found")
    return pkg


@evidence_router.get("/evidence/{evidence_id}/manifest")
def get_evidence_manifest(evidence_id: str) -> Dict[str, Any]:
    """Retrieves the full canonical JSON evidence manifest for inspection."""
    try:
        return evidence_service.get_evidence_manifest(evidence_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@evidence_router.get("/evidence/{evidence_id}/anchor", response_model=LedgerAnchorResponse)
def get_evidence_anchor(evidence_id: str):
    """Retrieves the immutable private ledger transaction receipt for an evidence package."""
    anchor = ledger_service.get_anchor(evidence_id)
    if not anchor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No ledger anchor found for {evidence_id}")
    return LedgerAnchorResponse(**anchor)


@evidence_router.post("/evidence/{evidence_id}/verify", response_model=EvidenceVerificationResponse)
def verify_evidence_integrity(evidence_id: str, payload: Optional[VerifyEvidenceRequest] = None):
    """
    Recalculates the SHA-256 hash of the off-chain stored evidence manifest
    and cryptographically verifies it against the immutable ledger anchor.
    Returns AUTHENTIC or TAMPERED.
    """
    req = payload or VerifyEvidenceRequest()
    try:
        return evidence_service.verify_evidence_integrity(
            evidence_id=evidence_id,
            operator_id=req.operator_id,
            role=req.role
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@evidence_router.post("/evidence/{evidence_id}/tamper-demo")
def tamper_evidence_for_demo(evidence_id: str, payload: Optional[TamperDemoRequest] = None):
    """
    Hero Demo Feature: Intentionally modifies off-chain stored evidence on disk
    without altering the blockchain anchor to demonstrate tamper detection.
    """
    req = payload or TamperDemoRequest()
    try:
        return evidence_service.tamper_evidence_for_demo(
            evidence_id=evidence_id,
            tamper_field=req.tamper_field,
            tamper_value=req.tamper_value
        )
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@evidence_router.post("/evidence/{evidence_id}/restore-demo")
def restore_evidence_for_demo(evidence_id: str):
    """
    Hero Demo Feature: Restores the original authentic off-chain evidence manifest.
    """
    try:
        return evidence_service.restore_evidence_for_demo(evidence_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@evidence_router.get("/evidence/{evidence_id}/audit-trail", response_model=List[EvidenceAuditLogResponse])
def get_evidence_audit_trail(evidence_id: str):
    """Retrieves the chronological, immutable audit log for an evidence package."""
    return evidence_service.get_evidence_audit_trail(evidence_id)


@evidence_router.get("/ledger/blocks")
def get_ledger_block_history(limit: int = Query(default=20, ge=1, le=100)) -> List[Dict[str, Any]]:
    """Retrieves the chronological blockchain block history of the private immutable ledger."""
    return ledger_service.get_block_history(limit=limit)
