import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.models.sync import (
    SyncStatusResponse,
    SyncQueueItemResponse,
    SyncBatchRequest,
    SyncBatchResponse,
    SyncRetryResponse,
)
from backend.services.sync_service import sync_service
from backend.services.central_sync_receiver import central_sync_receiver

logger = logging.getLogger(__name__)

sync_router = APIRouter(prefix="/api/sync", tags=["Synchronization Engine"])


@sync_router.get(
    "/status",
    response_model=SyncStatusResponse,
    summary="Get Sync Engine & Queue Status",
    description="Returns aggregate queue counts, storage utilization, and active sync progress."
)
def get_sync_status():
    return sync_service.get_status()


@sync_router.get(
    "/queue",
    response_model=List[SyncQueueItemResponse],
    summary="Get Sync Queue Items",
    description="Returns list of durable sync queue items with optional status filtering."
)
def get_sync_queue(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, SYNCING, SYNCED, FAILED, RETRY_PENDING)"),
    limit: int = Query(100, ge=1, le=500, description="Max items to return")
):
    return sync_service.get_queue_items(status=status, limit=limit)


@sync_router.post(
    "/start",
    summary="Trigger Sync Execution",
    description="Manually initiates a synchronization batch to central systems."
)
def trigger_sync(force: bool = Query(False, description="Force sync attempt even if state was flagged offline")):
    res = sync_service.trigger_sync(force=force)
    return res


@sync_router.post(
    "/retry/{item_id}",
    response_model=SyncRetryResponse,
    summary="Retry Specific Failed Queue Item",
    description="Resets attempt counters and marks failed queue item for immediate retry."
)
def retry_sync_item(item_id: int):
    res = sync_service.retry_item(item_id)
    if res.status == "error":
        raise HTTPException(status_code=404, detail=res.message)
    return res


@sync_router.post(
    "/batch",
    response_model=SyncBatchResponse,
    summary="Central Sync Batch Receiver",
    description="Idempotent central ingestion endpoint receiving offline batches from edge nodes."
)
def central_receive_batch(batch_req: SyncBatchRequest):
    return central_sync_receiver.process_batch(batch_req)
