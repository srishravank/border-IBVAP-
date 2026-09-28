import json
import logging
import math
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from backend.config import settings
from backend.database.connection import SessionLocal
from backend.database.models import (
    SyncQueueItemModel,
    SyncHistoryModel,
    EvidencePackageModel,
    LedgerAnchorModel,
)
from backend.models.sync import (
    ConnectionState,
    SyncQueueItemResponse,
    SyncQueueSummary,
    SyncStatusResponse,
    SyncPayload,
    SyncBatchRequest,
    SyncRetryResponse,
)
from backend.services.connectivity_service import connectivity_service
from backend.services.central_sync_receiver import central_sync_receiver
from backend.services.ledger_service import ledger_service

logger = logging.getLogger(__name__)


class SyncService:
    """
    Durable, resumable, priority-ordered Synchronization Engine for IBVAP 2.0.
    Handles queue ingestion, exponential backoff retries, idempotent sync execution,
    and deferred evidence anchoring.
    """

    def __init__(self):
        # Register callback with connectivity service to trigger sync upon reconnection
        connectivity_service.register_callback(self._on_connectivity_changed)

    def _on_connectivity_changed(self, old_state: ConnectionState, new_state: ConnectionState):
        """Callback invoked when connectivity state transitions."""
        if new_state in (ConnectionState.RECONNECTING, ConnectionState.ONLINE) and old_state == ConnectionState.OFFLINE:
            logger.info("[SYNC] Connectivity restored. Automatically triggering sync queue processing.")
            self.trigger_sync()

    def generate_idempotency_key(self, entity_type: str, entity_id: str, operation: str = "CREATE") -> str:
        """Constructs a deterministic, unique idempotency key for an edge record."""
        return f"{settings.EDGE_ID}-{entity_type}-{entity_id}-{operation}"

    def enqueue_item(
        self,
        entity_type: str,
        entity_id: str,
        payload: Dict[str, Any],
        operation: str = "CREATE",
        priority: Optional[int] = None,
        created_at: Optional[datetime] = None,
        idempotency_key: Optional[str] = None
    ) -> SyncQueueItemModel:
        """
        Enqueues an item into the durable local synchronization queue.
        Calculates priority automatically from risk level/evidence if not provided.
        """
        if priority is None:
            # Automatic priority determination
            if entity_type == "EVIDENCE_PACKAGE" or payload.get("risk_level") in ("CRITICAL", "HIGH"):
                priority = 1
            elif payload.get("risk_level") == "MEDIUM" or entity_type in ("INCIDENT", "EVENT"):
                priority = 2
            else:
                priority = 3

        if not idempotency_key:
            idempotency_key = self.generate_idempotency_key(entity_type, entity_id, operation)

        edge_ts = created_at or datetime.now(timezone.utc)

        db = SessionLocal()
        try:
            # Check for existing idempotency key to prevent queue duplicate entries
            existing = db.query(SyncQueueItemModel).filter(
                SyncQueueItemModel.idempotency_key == idempotency_key
            ).first()

            if existing:
                if existing.status in ("FAILED", "RETRY_PENDING"):
                    existing.status = "PENDING"
                    existing.attempt_count = 0
                    existing.next_retry_at = None
                    existing.payload_json = json.dumps(payload)
                    db.commit()
                    db.refresh(existing)
                return existing

            queue_item = SyncQueueItemModel(
                edge_id=settings.EDGE_ID,
                idempotency_key=idempotency_key,
                entity_type=entity_type,
                entity_id=entity_id,
                operation=operation,
                priority=priority,
                status="PENDING",
                payload_json=json.dumps(payload),
                attempt_count=0,
                created_at=edge_ts
            )
            db.add(queue_item)
            db.commit()
            db.refresh(queue_item)

            logger.info(f"[SYNC QUEUE] Enqueued {entity_type} {entity_id} (Priority: {priority}, Key: {idempotency_key})")

            # If online, attempt non-blocking sync
            if connectivity_service.is_online and settings.SYNC_ENABLED:
                self.trigger_sync()

            return queue_item
        finally:
            db.close()

    def get_pending_items(self, batch_size: int = 50) -> List[SyncQueueItemModel]:
        """Fetches pending items ordered by priority (1 before 2, 2 before 3) and timestamp."""
        db = SessionLocal()
        try:
            now_utc = datetime.now(timezone.utc)
            items = db.query(SyncQueueItemModel).filter(
                SyncQueueItemModel.status.in_(["PENDING", "RETRY_PENDING"])
            ).filter(
                (SyncQueueItemModel.next_retry_at == None) | (SyncQueueItemModel.next_retry_at <= now_utc)
            ).order_by(
                SyncQueueItemModel.priority.asc(),
                SyncQueueItemModel.created_at.asc()
            ).limit(batch_size).all()
            return items
        finally:
            db.close()

    def trigger_sync(self, force: bool = False) -> Dict[str, Any]:
        """
        Processes pending sync queue items in batches, sends to central sync receiver,
        updates statuses, handles retries with exponential backoff, and anchors deferred evidence.
        """
        if not connectivity_service.is_online and not force:
            logger.info("[SYNC] System is OFFLINE. Synchronization deferred until connectivity returns.")
            return {"status": "deferred", "message": "System is currently offline.", "synced_count": 0}

        # Transition state to SYNCING
        original_state = connectivity_service.current_state
        connectivity_service.set_state(ConnectionState.SYNCING, reason="Processing queued synchronization batch")

        start_time = time.time()
        total_synced = 0
        total_failed = 0
        import uuid
        batch_counter = 0

        while True:
            items = self.get_pending_items(batch_size=settings.SYNC_BATCH_SIZE)
            if not items:
                break

            batch_counter += 1
            batch_id = f"BATCH-{settings.EDGE_ID}-{int(time.time() * 1000)}-{batch_counter}-{uuid.uuid4().hex[:4]}"

            # Convert to SyncPayloads
            payload_list = [
                SyncPayload(
                    edge_id=it.edge_id,
                    idempotency_key=it.idempotency_key,
                    entity_type=it.entity_type,
                    entity_id=it.entity_id,
                    operation=it.operation,
                    priority=it.priority,
                    created_at_edge=it.created_at.isoformat(),
                    payload=it.payload
                )
                for it in items
            ]

            batch_req = SyncBatchRequest(
                edge_id=settings.EDGE_ID,
                batch_id=batch_id,
                items=payload_list,
                sent_at=datetime.now(timezone.utc).isoformat()
            )

            # Send to central sync receiver (or HTTP client in remote setup)
            batch_res = central_sync_receiver.process_batch(batch_req)

            # Map results back to queue items
            receipt_map = {r.idempotency_key: r for r in batch_res.receipts}

            db = SessionLocal()
            try:
                now_utc = datetime.now(timezone.utc)
                for it in items:
                    db_item = db.query(SyncQueueItemModel).filter(SyncQueueItemModel.id == it.id).first()
                    if not db_item:
                        continue

                    receipt = receipt_map.get(db_item.idempotency_key)
                    db_item.last_attempt_at = now_utc

                    if receipt and receipt.status in ("ACCEPTED", "DUPLICATE_ACCEPTED"):
                        db_item.status = "SYNCED"
                        db_item.synced_at = now_utc
                        db_item.error_message = None
                        total_synced += 1

                        # Deferred Phase 7 Evidence Anchoring Integration
                        if db_item.entity_type == "EVIDENCE_PACKAGE":
                            self._confirm_deferred_evidence_anchor(db, db_item.entity_id)

                    else:
                        db_item.attempt_count += 1
                        err_msg = receipt.message if receipt else "No receipt returned from central receiver"
                        db_item.error_message = err_msg

                        if db_item.attempt_count >= settings.SYNC_RETRY_LIMIT:
                            db_item.status = "FAILED"
                            total_failed += 1
                            logger.error(f"[SYNC] Item {db_item.idempotency_key} reached max retry limit ({settings.SYNC_RETRY_LIMIT}). Marked FAILED.")
                        else:
                            db_item.status = "RETRY_PENDING"
                            # Exponential backoff: backoff_base * 2^(attempt - 1)
                            backoff_seconds = settings.SYNC_RETRY_BACKOFF_BASE * math.pow(2, db_item.attempt_count - 1)
                            db_item.next_retry_at = now_utc + timedelta(seconds=backoff_seconds)
                            logger.warning(f"[SYNC] Item {db_item.idempotency_key} retry pending in {backoff_seconds:.1f}s (Attempt {db_item.attempt_count})")

                db.commit()
            finally:
                db.close()

        duration_ms = (time.time() - start_time) * 1000

        # Record batch history
        db = SessionLocal()
        try:
            hist = SyncHistoryModel(
                sync_id=f"SYNC-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}",
                edge_id=settings.EDGE_ID,
                status="SUCCESS" if total_failed == 0 else ("PARTIAL" if total_synced > 0 else "FAILED"),
                items_synced=total_synced,
                items_failed=total_failed,
                duration_ms=duration_ms,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(hist)
            db.commit()
        finally:
            db.close()

        # Restore online state
        connectivity_service.set_state(ConnectionState.ONLINE, reason="Sync completed successfully")

        logger.info(f"[SYNC] Batch completed: {total_synced} synced, {total_failed} failed in {duration_ms:.1f}ms")
        return {
            "status": "completed",
            "items_synced": total_synced,
            "items_failed": total_failed,
            "duration_ms": duration_ms
        }

    def _confirm_deferred_evidence_anchor(self, db, evidence_id: str):
        """
        When an offline evidence package is synchronized, confirms ledger anchoring
        and ensures status transitions from ANCHOR_PENDING to ANCHORED without modifying hash.
        """
        pkg = db.query(EvidencePackageModel).filter(EvidencePackageModel.evidence_id == evidence_id).first()
        if pkg:
            pkg.status = "ANCHORED"
            # Ensure anchor model exists in confirmed state
            anchor = db.query(LedgerAnchorModel).filter(LedgerAnchorModel.evidence_id == evidence_id).first()
            if anchor:
                anchor.status = "CONFIRMED"
            logger.info(f"[SYNC] Evidence package {evidence_id} ledger status confirmed ANCHORED.")

    def retry_item(self, item_id: int) -> SyncRetryResponse:
        """Manually resets and retries a failed queue item."""
        db = SessionLocal()
        try:
            item = db.query(SyncQueueItemModel).filter(SyncQueueItemModel.id == item_id).first()
            if not item:
                return SyncRetryResponse(status="error", message=f"Item {item_id} not found", item_id=item_id, next_status="UNKNOWN")

            item.status = "PENDING"
            item.attempt_count = 0
            item.next_retry_at = None
            item.error_message = None
            db.commit()

            if connectivity_service.is_online:
                self.trigger_sync()

            return SyncRetryResponse(
                status="success",
                message=f"Item {item_id} queued for immediate retry",
                item_id=item_id,
                next_status="PENDING"
            )
        finally:
            db.close()

    def get_summary(self) -> SyncQueueSummary:
        """Calculates current sync queue breakdown."""
        db = SessionLocal()
        try:
            total = db.query(SyncQueueItemModel).count()
            pending = db.query(SyncQueueItemModel).filter(SyncQueueItemModel.status == "PENDING").count()
            syncing = db.query(SyncQueueItemModel).filter(SyncQueueItemModel.status == "SYNCING").count()
            synced = db.query(SyncQueueItemModel).filter(SyncQueueItemModel.status == "SYNCED").count()
            failed = db.query(SyncQueueItemModel).filter(SyncQueueItemModel.status == "FAILED").count()
            retry_pending = db.query(SyncQueueItemModel).filter(SyncQueueItemModel.status == "RETRY_PENDING").count()
            
            # Evidence packages pending anchoring
            ev_pending = db.query(SyncQueueItemModel).filter(
                SyncQueueItemModel.entity_type == "EVIDENCE_PACKAGE",
                SyncQueueItemModel.status.in_(["PENDING", "RETRY_PENDING"])
            ).count()

            latest_hist = db.query(SyncHistoryModel).filter(
                SyncHistoryModel.status.in_(["SUCCESS", "PARTIAL"])
            ).order_by(SyncHistoryModel.id.desc()).first()

            return SyncQueueSummary(
                total_queued=total,
                pending_count=pending,
                syncing_count=syncing,
                synced_count=synced,
                failed_count=failed,
                retry_pending_count=retry_pending,
                evidence_pending_count=ev_pending,
                last_successful_sync=latest_hist.timestamp.isoformat() if latest_hist else None,
                storage_used_bytes=1024 * 1024 * (total * 2),  # Estimated local storage usage
                storage_limit_bytes=settings.MAX_LOCAL_STORAGE_MB * 1024 * 1024
            )
        finally:
            db.close()

    def get_queue_items(self, status: Optional[str] = None, limit: int = 100) -> List[SyncQueueItemResponse]:
        """Returns list of queue items for SOC inspection."""
        db = SessionLocal()
        try:
            query = db.query(SyncQueueItemModel)
            if status:
                query = query.filter(SyncQueueItemModel.status == status)
            items = query.order_by(SyncQueueItemModel.id.desc()).limit(limit).all()

            return [
                SyncQueueItemResponse(
                    id=it.id,
                    edge_id=it.edge_id,
                    idempotency_key=it.idempotency_key,
                    entity_type=it.entity_type,
                    entity_id=it.entity_id,
                    operation=it.operation,
                    priority=it.priority,
                    status=it.status,
                    payload=it.payload,
                    attempt_count=it.attempt_count,
                    created_at=it.created_at.isoformat(),
                    last_attempt_at=it.last_attempt_at.isoformat() if it.last_attempt_at else None,
                    next_retry_at=it.next_retry_at.isoformat() if it.next_retry_at else None,
                    synced_at=it.synced_at.isoformat() if it.synced_at else None,
                    error_message=it.error_message
                )
                for it in items
            ]
        finally:
            db.close()

    def get_status(self) -> SyncStatusResponse:
        """Returns overall sync engine status."""
        return SyncStatusResponse(
            edge_id=settings.EDGE_ID,
            connectivity=connectivity_service.get_status(),
            summary=self.get_summary(),
            active_batch_in_progress=(connectivity_service.current_state == ConnectionState.SYNCING)
        )


sync_service = SyncService()
