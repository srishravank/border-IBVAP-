from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConnectionState(str, Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    RECONNECTING = "RECONNECTING"
    SYNCING = "SYNCING"


class SyncStatus(str, Enum):
    PENDING = "PENDING"
    SYNCING = "SYNCING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"
    RETRY_PENDING = "RETRY_PENDING"


class ConnectivityStatusResponse(BaseModel):
    edge_id: str
    state: ConnectionState
    is_simulated: bool = False
    reason: str = "Normal operation"
    checked_at: str
    heartbeat_interval_seconds: float
    central_server_url: str = "http://central-command.ibvap.internal/api"


class ConnectivitySimulationRequest(BaseModel):
    state: ConnectionState = Field(..., description="Target connection state (e.g. OFFLINE, ONLINE)")
    reason: Optional[str] = Field("Manual operator simulation", description="Reason for the simulation override")


class SyncQueueItemResponse(BaseModel):
    id: int
    edge_id: str
    idempotency_key: str
    entity_type: str
    entity_id: str
    operation: str
    priority: int
    status: str
    payload: Dict[str, Any]
    attempt_count: int
    created_at: str
    last_attempt_at: Optional[str] = None
    next_retry_at: Optional[str] = None
    synced_at: Optional[str] = None
    error_message: Optional[str] = None


class SyncQueueSummary(BaseModel):
    total_queued: int
    pending_count: int
    syncing_count: int
    synced_count: int
    failed_count: int
    retry_pending_count: int
    evidence_pending_count: int
    last_successful_sync: Optional[str] = None
    storage_used_bytes: int = 0
    storage_limit_bytes: int = 5120 * 1024 * 1024


class SyncStatusResponse(BaseModel):
    edge_id: str
    connectivity: ConnectivityStatusResponse
    summary: SyncQueueSummary
    active_batch_in_progress: bool = False
    current_progress: Optional[Dict[str, Any]] = None


class SyncPayload(BaseModel):
    edge_id: str
    idempotency_key: str
    entity_type: str
    entity_id: str
    operation: str
    priority: int = 2
    created_at_edge: str
    payload: Dict[str, Any]


class SyncBatchRequest(BaseModel):
    edge_id: str
    batch_id: str
    items: List[SyncPayload]
    sent_at: str


class SyncBatchReceipt(BaseModel):
    idempotency_key: str
    entity_type: str
    entity_id: str
    status: str  # "ACCEPTED", "DUPLICATE_ACCEPTED", "REJECTED"
    synced_at: str
    message: Optional[str] = None


class SyncBatchResponse(BaseModel):
    batch_id: str
    edge_id: str
    processed_count: int
    accepted_count: int
    duplicate_count: int
    failed_count: int
    receipts: List[SyncBatchReceipt]
    received_at: str


class SyncRetryResponse(BaseModel):
    status: str
    message: str
    item_id: int
    next_status: str
