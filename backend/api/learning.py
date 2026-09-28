from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.models.learning import (
    ModelVersionResponse,
    ModelValidationResponse,
    TrainingSampleResponse,
    SampleReviewRequest,
    LocalTrainingStartRequest,
    LocalTrainingStatusResponse,
    TrainingRunResponse,
    ModelUpdateResponse,
    FederatedRoundResponse,
    CreateFederatedRoundRequest,
    ModelApprovalRequest,
    ModelDeploymentRequest,
    ModelRollbackRequest,
    ModelAuditLogResponse,
    PrivacyStatusResponse
)
from backend.services.model_registry_service import model_registry
from backend.services.training_sample_service import training_sample_service
from backend.services.local_training_service import local_training_service
from backend.services.federated_learning_service import federated_aggregator

router = APIRouter(prefix="", tags=["Phase 9: On-Device & Federated Learning"])


# --- Model Registry Endpoints ---

@router.get("/models", response_model=List[ModelVersionResponse])
async def list_models(status: Optional[str] = Query(None, description="Filter by status (ACTIVE, CANDIDATE, ARCHIVED, REJECTED)")):
    """Lists all registered models."""
    models = model_registry.list_models(status=status)
    return [
        ModelVersionResponse(
            model_id=m.model_id,
            version=m.version,
            parent_version=m.parent_version,
            model_type=m.model_type,
            model_hash=m.model_hash,
            training_round=m.training_round,
            status=m.status,
            validation_status=m.validation_status,
            metrics=m.metrics,
            model_metadata=m.model_metadata,
            created_by=m.created_by,
            created_at=m.created_at,
            approved_by=m.approved_by,
            approved_at=m.approved_at,
            deployed_at=m.deployed_at
        )
        for m in models
    ]


@router.get("/models/active", response_model=ModelVersionResponse)
async def get_active_model():
    """Returns the currently active production detection model."""
    m = model_registry.get_active_model()
    if not m:
        raise HTTPException(status_code=404, detail="No active model found.")
    return ModelVersionResponse(
        model_id=m.model_id,
        version=m.version,
        parent_version=m.parent_version,
        model_type=m.model_type,
        model_hash=m.model_hash,
        training_round=m.training_round,
        status=m.status,
        validation_status=m.validation_status,
        metrics=m.metrics,
        model_metadata=m.model_metadata,
        created_by=m.created_by,
        created_at=m.created_at,
        approved_by=m.approved_by,
        approved_at=m.approved_at,
        deployed_at=m.deployed_at
    )


@router.get("/models/candidates", response_model=List[ModelVersionResponse])
async def list_candidate_models():
    """Lists all candidate models awaiting validation or supervisor review."""
    candidates = model_registry.get_candidate_models()
    return [
        ModelVersionResponse(
            model_id=m.model_id,
            version=m.version,
            parent_version=m.parent_version,
            model_type=m.model_type,
            model_hash=m.model_hash,
            training_round=m.training_round,
            status=m.status,
            validation_status=m.validation_status,
            metrics=m.metrics,
            model_metadata=m.model_metadata,
            created_by=m.created_by,
            created_at=m.created_at,
            approved_by=m.approved_by,
            approved_at=m.approved_at,
            deployed_at=m.deployed_at
        )
        for m in candidates
    ]


@router.get("/models/{model_id}", response_model=ModelVersionResponse)
async def get_model(model_id: str):
    """Retrieves details of a specific model by ID."""
    m = model_registry.get_model(model_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
    return ModelVersionResponse(
        model_id=m.model_id,
        version=m.version,
        parent_version=m.parent_version,
        model_type=m.model_type,
        model_hash=m.model_hash,
        training_round=m.training_round,
        status=m.status,
        validation_status=m.validation_status,
        metrics=m.metrics,
        model_metadata=m.model_metadata,
        created_by=m.created_by,
        created_at=m.created_at,
        approved_by=m.approved_by,
        approved_at=m.approved_at,
        deployed_at=m.deployed_at
    )


@router.get("/models/{model_id}/metrics")
async def get_model_metrics(model_id: str):
    """Retrieves measured evaluation metrics for a specific model."""
    m = model_registry.get_model(model_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
    return {
        "model_id": m.model_id,
        "version": m.version,
        "status": m.status,
        "validation_status": m.validation_status,
        "metrics": m.metrics
    }


@router.get("/models/{model_id}/audit", response_model=List[ModelAuditLogResponse])
async def get_model_audit_logs(model_id: str, limit: int = Query(50, ge=1, le=200)):
    """Retrieves the governance audit trail for a model."""
    logs = model_registry.get_model_audit_logs(model_id=model_id, limit=limit)
    return [
        ModelAuditLogResponse(
            log_id=l.log_id,
            model_id=l.model_id,
            action=l.action,
            actor=l.actor,
            role=l.role,
            timestamp=l.timestamp,
            log_metadata=l.log_metadata
        )
        for l in logs
    ]


@router.post("/models/{model_id}/validate", response_model=ModelValidationResponse)
async def validate_candidate_model(model_id: str):
    """Executes benchmark validation and comparison between candidate and active models."""
    try:
        res = model_registry.validate_candidate(model_id)
        return ModelValidationResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/models/{model_id}/approve", response_model=ModelVersionResponse)
async def approve_candidate_model(model_id: str, payload: ModelApprovalRequest):
    """Supervisor/Admin review gate approving candidate model for deployment."""
    try:
        m = model_registry.approve_model(
            model_id=model_id,
            actor=payload.operator_id,
            role=payload.role,
            notes=payload.notes
        )
        return ModelVersionResponse(
            model_id=m.model_id,
            version=m.version,
            parent_version=m.parent_version,
            model_type=m.model_type,
            model_hash=m.model_hash,
            training_round=m.training_round,
            status=m.status,
            validation_status=m.validation_status,
            metrics=m.metrics,
            model_metadata=m.model_metadata,
            created_by=m.created_by,
            created_at=m.created_at,
            approved_by=m.approved_by,
            approved_at=m.approved_at,
            deployed_at=m.deployed_at
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/models/{model_id}/reject", response_model=ModelVersionResponse)
async def reject_candidate_model(model_id: str, payload: ModelApprovalRequest):
    """Supervisor/Admin review gate rejecting candidate model."""
    try:
        m = model_registry.reject_model(
            model_id=model_id,
            actor=payload.operator_id,
            role=payload.role,
            notes=payload.notes
        )
        return ModelVersionResponse(
            model_id=m.model_id,
            version=m.version,
            parent_version=m.parent_version,
            model_type=m.model_type,
            model_hash=m.model_hash,
            training_round=m.training_round,
            status=m.status,
            validation_status=m.validation_status,
            metrics=m.metrics,
            model_metadata=m.model_metadata,
            created_by=m.created_by,
            created_at=m.created_at,
            approved_by=m.approved_by,
            approved_at=m.approved_at,
            deployed_at=m.deployed_at
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/models/{model_id}/deploy", response_model=ModelVersionResponse)
async def deploy_model(model_id: str, payload: ModelDeploymentRequest):
    """Admin deploys approved candidate model with smoke tests and backup."""
    try:
        m = model_registry.deploy_model(
            model_id=model_id,
            actor=payload.operator_id,
            role=payload.role,
            notes=payload.notes
        )
        return ModelVersionResponse(
            model_id=m.model_id,
            version=m.version,
            parent_version=m.parent_version,
            model_type=m.model_type,
            model_hash=m.model_hash,
            training_round=m.training_round,
            status=m.status,
            validation_status=m.validation_status,
            metrics=m.metrics,
            model_metadata=m.model_metadata,
            created_by=m.created_by,
            created_at=m.created_at,
            approved_by=m.approved_by,
            approved_at=m.approved_at,
            deployed_at=m.deployed_at
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/models/rollback", response_model=Dict[str, Any])
async def rollback_active_model(payload: ModelRollbackRequest):
    """Rolls back the active model to the previously archived version."""
    try:
        restored, demoted = model_registry.rollback_model(
            actor=payload.operator_id,
            role=payload.role,
            reason=payload.reason
        )
        return {
            "status": "ROLLBACK_SUCCESSFUL",
            "restored_model_id": restored.model_id,
            "restored_version": restored.version,
            "demoted_model_id": demoted.model_id,
            "demoted_version": demoted.version,
            "reason": payload.reason
        }
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/models/{model_id}/verify-integrity")
async def verify_model_integrity(model_id: str):
    """Verifies that a model's stored SHA-256 hash matches its computed descriptor."""
    try:
        return model_registry.verify_model_integrity(model_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Training Samples Endpoints ---

@router.get("/training/samples", response_model=List[TrainingSampleResponse])
async def list_training_samples(
    status: Optional[str] = Query(None, description="PENDING, VALIDATED, REJECTED"),
    label: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500)
):
    """Lists training samples with validation provenance."""
    samples = training_sample_service.list_samples(validation_status=status, label=label, limit=limit)
    return [
        TrainingSampleResponse(
            sample_id=s.sample_id,
            edge_id=s.edge_id,
            camera_id=s.camera_id,
            source_event_id=s.source_event_id,
            label=s.label,
            label_source=s.label_source,
            validation_status=s.validation_status,
            confidence=s.confidence,
            bbox=s.bbox,
            reviewed_by=s.reviewed_by,
            reviewed_at=s.reviewed_at,
            created_at=s.created_at,
            sample_metadata=s.sample_metadata
        )
        for s in samples
    ]


@router.post("/training/samples/{sample_id}/approve", response_model=TrainingSampleResponse)
async def approve_training_sample(sample_id: str, payload: SampleReviewRequest):
    """Human-in-the-loop validation: Operator approves training sample."""
    try:
        s = training_sample_service.review_sample(
            sample_id=sample_id,
            action="APPROVE",
            operator_id=payload.operator_id,
            role=payload.role,
            notes=payload.notes
        )
        return TrainingSampleResponse(
            sample_id=s.sample_id,
            edge_id=s.edge_id,
            camera_id=s.camera_id,
            source_event_id=s.source_event_id,
            label=s.label,
            label_source=s.label_source,
            validation_status=s.validation_status,
            confidence=s.confidence,
            bbox=s.bbox,
            reviewed_by=s.reviewed_by,
            reviewed_at=s.reviewed_at,
            created_at=s.created_at,
            sample_metadata=s.sample_metadata
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/training/samples/{sample_id}/reject", response_model=TrainingSampleResponse)
async def reject_training_sample(sample_id: str, payload: SampleReviewRequest):
    """Human-in-the-loop validation: Operator rejects training sample."""
    try:
        s = training_sample_service.review_sample(
            sample_id=sample_id,
            action="REJECT",
            operator_id=payload.operator_id,
            role=payload.role,
            notes=payload.notes
        )
        return TrainingSampleResponse(
            sample_id=s.sample_id,
            edge_id=s.edge_id,
            camera_id=s.camera_id,
            source_event_id=s.source_event_id,
            label=s.label,
            label_source=s.label_source,
            validation_status=s.validation_status,
            confidence=s.confidence,
            bbox=s.bbox,
            reviewed_by=s.reviewed_by,
            reviewed_at=s.reviewed_at,
            created_at=s.created_at,
            sample_metadata=s.sample_metadata
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/training/samples/{sample_id}/relabel", response_model=TrainingSampleResponse)
async def relabel_training_sample(sample_id: str, payload: SampleReviewRequest):
    """Human-in-the-loop validation: Operator relabels and validates training sample."""
    try:
        s = training_sample_service.review_sample(
            sample_id=sample_id,
            action="RELABEL",
            corrected_label=payload.corrected_label,
            operator_id=payload.operator_id,
            role=payload.role,
            notes=payload.notes
        )
        return TrainingSampleResponse(
            sample_id=s.sample_id,
            edge_id=s.edge_id,
            camera_id=s.camera_id,
            source_event_id=s.source_event_id,
            label=s.label,
            label_source=s.label_source,
            validation_status=s.validation_status,
            confidence=s.confidence,
            bbox=s.bbox,
            reviewed_by=s.reviewed_by,
            reviewed_at=s.reviewed_at,
            created_at=s.created_at,
            sample_metadata=s.sample_metadata
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Local Training Endpoints ---

@router.get("/training/status", response_model=LocalTrainingStatusResponse)
async def get_training_status():
    """Returns local edge training status, validated samples, and resource limits."""
    res = local_training_service.get_status()
    return LocalTrainingStatusResponse(**res)


@router.post("/training/start", response_model=TrainingRunResponse)
async def start_local_training(payload: LocalTrainingStartRequest):
    """Initiates a controlled on-device fine-tuning run."""
    try:
        run = local_training_service.start_training(
            epochs=payload.epochs,
            batch_size=payload.batch_size,
            learning_rate=payload.learning_rate,
            device=payload.device,
            simulation_mode=payload.simulation_mode,
            operator_id=payload.operator_id,
            role=payload.role
        )
        return TrainingRunResponse(
            run_id=run.run_id,
            edge_id=run.edge_id,
            base_model_version=run.base_model_version,
            sample_count=run.sample_count,
            epochs=run.epochs,
            batch_size=run.batch_size,
            learning_rate=run.learning_rate,
            status=run.status,
            training_loss=run.training_loss,
            validation_metric=run.validation_metric,
            metrics=run.metrics,
            error_message=run.error_message,
            started_at=run.started_at,
            completed_at=run.completed_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/training/runs", response_model=List[TrainingRunResponse])
async def list_training_runs(limit: int = Query(50, ge=1, le=200)):
    """Lists local training runs."""
    runs = local_training_service.list_training_runs(limit=limit)
    return [
        TrainingRunResponse(
            run_id=r.run_id,
            edge_id=r.edge_id,
            base_model_version=r.base_model_version,
            sample_count=r.sample_count,
            epochs=r.epochs,
            batch_size=r.batch_size,
            learning_rate=r.learning_rate,
            status=r.status,
            training_loss=r.training_loss,
            validation_metric=r.validation_metric,
            metrics=r.metrics,
            error_message=r.error_message,
            started_at=r.started_at,
            completed_at=r.completed_at
        )
        for r in runs
    ]


@router.get("/training/updates", response_model=List[ModelUpdateResponse])
async def list_model_updates(limit: int = Query(50, ge=1, le=200)):
    """Lists generated model updates."""
    updates = local_training_service.list_model_updates(limit=limit)
    return [
        ModelUpdateResponse(
            update_id=u.update_id,
            edge_id=u.edge_id,
            base_model_version=u.base_model_version,
            training_round=u.training_round,
            sample_count=u.sample_count,
            training_loss=u.training_loss,
            validation_metric=u.validation_metric,
            update_hash=u.update_hash,
            status=u.status,
            created_at=u.created_at,
            metrics=u.metrics
        )
        for u in updates
    ]


# --- Federated Learning Endpoints ---

@router.get("/federated/rounds", response_model=List[FederatedRoundResponse])
async def list_federated_rounds():
    """Lists all federated aggregation rounds."""
    rounds = federated_aggregator.list_rounds()
    return [
        FederatedRoundResponse(
            round_id=rd.round_id,
            base_model_version=rd.base_model_version,
            participants=rd.participants,
            updates_received=rd.updates_received,
            aggregation_method=rd.aggregation_method,
            candidate_model_id=rd.candidate_model_id,
            status=rd.status,
            error_message=rd.error_message,
            created_at=rd.created_at,
            completed_at=rd.completed_at
        )
        for rd in rounds
    ]


@router.post("/federated/rounds", response_model=FederatedRoundResponse)
async def create_federated_round(payload: CreateFederatedRoundRequest):
    """Creates a new federated aggregation round."""
    try:
        r = federated_aggregator.create_round(
            base_model_version=payload.base_model_version,
            participating_edges=payload.participating_edges,
            aggregation_method=payload.aggregation_method,
            operator_id=payload.operator_id,
            role=payload.role
        )
        return FederatedRoundResponse(
            round_id=r.round_id,
            base_model_version=r.base_model_version,
            participants=r.participants,
            updates_received=r.updates_received,
            aggregation_method=r.aggregation_method,
            candidate_model_id=r.candidate_model_id,
            status=r.status,
            error_message=r.error_message,
            created_at=r.created_at,
            completed_at=r.completed_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/federated/rounds/{round_id}", response_model=FederatedRoundResponse)
async def get_federated_round(round_id: str):
    """Retrieves details of a federated aggregation round."""
    r = federated_aggregator.get_round(round_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Federated round '{round_id}' not found.")
    return FederatedRoundResponse(
        round_id=r.round_id,
        base_model_version=r.base_model_version,
        participants=r.participants,
        updates_received=r.updates_received,
        aggregation_method=r.aggregation_method,
        candidate_model_id=r.candidate_model_id,
        status=r.status,
        error_message=r.error_message,
        created_at=r.created_at,
        completed_at=r.completed_at
    )


@router.post("/federated/rounds/{round_id}/aggregate")
async def aggregate_federated_round(round_id: str):
    """Triggers weighted FedAvg aggregation for a federated round."""
    try:
        return federated_aggregator.aggregate_round(round_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/federated/privacy", response_model=PrivacyStatusResponse)
async def get_privacy_status():
    """Returns privacy status telemetry verifying zero raw video transmission."""
    res = federated_aggregator.get_privacy_status()
    return PrivacyStatusResponse(**res)
