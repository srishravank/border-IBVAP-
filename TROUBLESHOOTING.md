# IBVAP 2.0 — Troubleshooting & Diagnostic Guide

## 1. System Health Diagnostics

To verify system status and diagnose issues across any subsystem:

```bash
# Query unified health endpoint
curl http://localhost:8000/api/system/health
```

Expected output when healthy:
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "camera_pipeline": "healthy",
    "ai_engine": "healthy",
    "risk_engine": "healthy",
    "evidence": "healthy",
    "ledger": "healthy",
    "sync": "healthy",
    "learning": "ready"
  }
}
```

---

## 2. Common Issues & Solutions

### Issue 1: Camera Feed Disconnected or Frozen
- **Symptom:** Camera card displays `OFFLINE` or `FROZEN`.
- **Cause:** RTSP stream timeout, network disconnection, or corrupted video file path.
- **Resolution:**
  1. Check camera status via `/api/cameras`.
  2. Verify network connectivity to RTSP source.
  3. Ensure video file exists at configured storage path.
  4. CameraManager automatically attempts exponential backoff reconnection up to 10 attempts.

### Issue 2: Offline Synchronization Queue Stuck
- **Symptom:** Sync queue shows pending items after network connection is restored.
- **Cause:** Central sync endpoint unreachable or network packet drop.
- **Resolution:**
  1. Check connectivity state via `/api/connectivity/status`.
  2. Trigger immediate synchronization via `POST /api/sync/trigger`.
  3. Inspect failed items via `/api/sync/status` and retry individual item with `POST /api/sync/retry/{item_id}`.

### Issue 3: Evidence Package Verification Reports `TAMPERED`
- **Symptom:** Evidence verification displays `TAMPERED` status.
- **Cause:** Manifest JSON on disk was modified after blockchain anchoring.
- **Resolution:**
  1. Review detailed tamper diff in the UI or `/api/evidence/{evidence_id}/verify` output.
  2. If intentional for demonstration, click **Restore Authentic Evidence** (`POST /api/evidence/{evidence_id}/restore`) to restore the authentic manifest from clean backup.

### Issue 4: Model Deployment Blocked by RBAC
- **Symptom:** `403 Forbidden` error when attempting to approve or deploy candidate model.
- **Cause:** Current user role is `OPERATOR` or `INVESTIGATOR`.
- **Resolution:**
  1. Model approval requires `SUPERVISOR` or `ADMIN` role.
  2. Model deployment requires `ADMIN` role.
  3. Switch role in the UI header dropdown or pass `role: "ADMIN"` in the API request payload.

### Issue 5: Simulation State Reset
- **Symptom:** Need to start clean demonstration from scratch.
- **Resolution:**
  - Call the clean reset endpoint:
    ```bash
    curl -X POST http://localhost:8000/api/demo/reset
    ```
  - This resets all demo subjects, incidents, risk assessments, sync queues, and learning state while preserving the baseline production model (`MODEL-YOLO-V1.0.0`).

---

## 3. Diagnostic Commands

```bash
# 1. Run all unit & integration tests
pytest -v

# 2. Check SQLite database integrity
python -c "from backend.database.connection import SessionLocal; from sqlalchemy import text; db=SessionLocal(); print(db.execute(text('PRAGMA integrity_check;')).fetchall())"

# 3. Verify active AI model hash
python -c "from backend.services.model_registry_service import model_registry; m=model_registry.get_active_model(); print('Active Model:', m.version, 'Hash:', m.model_hash)"

# 4. Verify blockchain ledger integrity
python -c "from backend.services.ledger_service import ledger_service; print(ledger_service.verify_ledger_integrity())"
```
