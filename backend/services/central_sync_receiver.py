import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
from backend.models.sync import (
    SyncBatchRequest,
    SyncBatchResponse,
    SyncBatchReceipt,
    SyncPayload,
)

logger = logging.getLogger(__name__)


class CentralSyncReceiver:
    """
    Central Server Ingestion Receiver for IBVAP 2.0.
    Handles idempotent synchronization of offline-created records,
    guaranteeing deduplication, timestamp preservation, and deterministic receipts.
    """

    def __init__(self):
        # In-memory deduplication registry (in production backed by central DB / distributed cache)
        self._processed_keys: Dict[str, Dict[str, Any]] = {}

    def process_batch(self, batch_req: SyncBatchRequest) -> SyncBatchResponse:
        """
        Processes a batch of synchronized offline records idempotently.
        """
        receipts: List[SyncBatchReceipt] = []
        accepted_cnt = 0
        duplicate_cnt = 0
        failed_cnt = 0
        now_iso = datetime.now(timezone.utc).isoformat()

        for item in batch_req.items:
            key = item.idempotency_key
            if key in self._processed_keys:
                # Idempotent deduplication: already processed
                duplicate_cnt += 1
                receipts.append(SyncBatchReceipt(
                    idempotency_key=key,
                    entity_type=item.entity_type,
                    entity_id=item.entity_id,
                    status="DUPLICATE_ACCEPTED",
                    synced_at=self._processed_keys[key]["synced_at"],
                    message="Item previously synchronized. Deduplicated successfully."
                ))
                logger.info(f"[CENTRAL SYNC] Deduplicated existing key: {key}")
            else:
                # Fresh ingestion: record item
                try:
                    self._processed_keys[key] = {
                        "edge_id": item.edge_id,
                        "entity_type": item.entity_type,
                        "entity_id": item.entity_id,
                        "operation": item.operation,
                        "created_at_edge": item.created_at_edge,
                        "payload": item.payload,
                        "synced_at": now_iso
                    }
                    accepted_cnt += 1
                    receipts.append(SyncBatchReceipt(
                        idempotency_key=key,
                        entity_type=item.entity_type,
                        entity_id=item.entity_id,
                        status="ACCEPTED",
                        synced_at=now_iso,
                        message=f"Successfully synchronized {item.entity_type} {item.entity_id}."
                    ))
                    logger.info(f"[CENTRAL SYNC] Ingested {item.entity_type} {item.entity_id} (Edge: {item.edge_id}, Key: {key})")
                except Exception as e:
                    failed_cnt += 1
                    receipts.append(SyncBatchReceipt(
                        idempotency_key=key,
                        entity_type=item.entity_type,
                        entity_id=item.entity_id,
                        status="REJECTED",
                        synced_at=now_iso,
                        message=f"Ingestion failed: {str(e)}"
                    ))
                    logger.error(f"[CENTRAL SYNC] Failed to ingest key {key}: {e}")

        return SyncBatchResponse(
            batch_id=batch_req.batch_id,
            edge_id=batch_req.edge_id,
            processed_count=len(batch_req.items),
            accepted_count=accepted_cnt,
            duplicate_count=duplicate_cnt,
            failed_count=failed_cnt,
            receipts=receipts,
            received_at=now_iso
        )

    def is_processed(self, idempotency_key: str) -> bool:
        return idempotency_key in self._processed_keys

    def reset(self):
        self._processed_keys.clear()


central_sync_receiver = CentralSyncReceiver()
