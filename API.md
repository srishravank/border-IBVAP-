# IBVAP 2.0 — API Reference & Specification

Base URL: `http://localhost:8000/api`  
Interactive Swagger Docs: `http://localhost:8000/docs`

---

## 1. System Health & Telemetry

### `GET /api/system/health`
Returns structured operational status across all subsystems.

**Response:**
```json
{
  "status": "healthy",
  "system": "IBVAP 2.0 Intelligent Border Video Analytics & Evidence Platform",
  "phase": "PHASE 11 - FINAL VALIDATION & JURY READINESS (RC1)",
  "services": {
    "database": "healthy",
    "camera_pipeline": "healthy",
    "ai_engine": "healthy",
    "risk_engine": "healthy",
    "evidence": "healthy",
    "ledger": "healthy",
    "sync": "healthy",
    "learning": "ready",
    "demo_controller": "ready"
  },
  "metrics": {
    "total_cameras": 4,
    "online_cameras": 4,
    "aggregate_fps": 100.0,
    "total_frames_ingested": 15420
  }
}
```

---

## 2. Ingestion & Perception (Phases 1 & 2)

- `GET /api/cameras` — List all registered cameras and live health statuses.
- `POST /api/cameras` — Register a new camera stream (RTSP, File, Webcam).
- `GET /api/ai/status` — Live AI detection and tracking engine telemetry.
- `GET /api/ai/tracks/{camera_id}` — Active ByteTrack tracks for a specific camera.

---

## 3. Virtual Zones & Verification (Phase 3)

- `GET /api/zones` — List configured polygon virtual zones.
- `POST /api/zones` — Create a virtual fence or exclusion polygon.
- `GET /api/events` — Retrieve confirmed multi-frame verified security events.
- `GET /api/events/candidates` — Active unconfirmed candidates in the verification gate.

---

## 4. Cross-Camera Intelligence & Incident Graph (Phase 4)

- `GET /api/subjects` — List all global subjects and cross-camera trajectories.
- `GET /api/subjects/{subject_id}/journey` — Chronological multi-camera journey cards.
- `GET /api/incidents` — List all active and closed security incidents.
- `GET /api/incidents/{incident_id}/graph` — Topological node-edge incident graph.
- `GET /api/incidents/{incident_id}/timeline` — Microsecond-sorted incident timeline.

---

## 5. Explainable Risk Engine (Phase 5)

- `GET /api/risk/incidents/{incident_id}` — Explainable risk assessment with factor contributions.
- `GET /api/risk/config` — Current active risk weights and threshold configuration.
- `PUT /api/risk/config` — Update risk weights and night observation windows.

---

## 6. Command Center & Response (Phase 6)

- `GET /api/dashboard/summary` — High-level SOC metrics for overview wall.
- `GET /api/alerts` — Real-time high-risk security alert notifications.
- `GET /api/sectors/risk` — Threat level breakdown across border sectors.
- `GET /api/command/incidents/{incident_id}/recommended-cameras` — Forward-tracking camera suggestions.
- `POST /api/command/incidents/{incident_id}/acknowledge` — Acknowledge an incident.
- `POST /api/command/incidents/{incident_id}/notes` — Attach collaborative investigation notes.
- `POST /api/command/incidents/{incident_id}/transition` — Transition incident lifecycle status (`INVESTIGATING`, `CLOSED`).

---

## 7. Evidence Trust & Blockchain Ledger (Phase 7)

- `POST /api/evidence/generate` — Generate canonical tamper-evident evidence package.
- `GET /api/evidence/{evidence_id}` — Inspect stored evidence package.
- `POST /api/evidence/{evidence_id}/verify` — Recalculate SHA-256 hash and verify against blockchain ledger.
- `POST /api/evidence/{evidence_id}/tamper-demo` — Simulate off-chain evidence tampering.
- `POST /api/evidence/{evidence_id}/restore` — Restore authentic evidence manifest from clean backup.
- `GET /api/ledger/blocks` — Inspect private blockchain blocks and Merkle hash links.

---

## 8. Offline-First & Resilient Sync (Phase 8)

- `GET /api/connectivity/status` — Network connectivity status (`ONLINE`, `OFFLINE`, `RECONNECTING`).
- `POST /api/connectivity/simulate` — Toggle simulated offline mode.
- `GET /api/sync/status` — Inspect durable sync queue summary and pending items.
- `POST /api/sync/trigger` — Trigger immediate batch synchronization with central server.
- `POST /api/sync/retry/{item_id}` — Retry a failed synchronization queue item.

---

## 9. On-Device & Federated Learning (Phase 9)

- `GET /api/models` — List registered AI models in model registry.
- `GET /api/models/active` — Inspect active production edge model and SHA-256 weight hash.
- `GET /api/models/candidates` — List pending candidate models awaiting review.
- `POST /api/models/{model_id}/validate` — Run automated benchmark validation comparison (+mAP gain).
- `POST /api/models/{model_id}/approve` — Supervisor RBAC approval for candidate model.
- `POST /api/models/{model_id}/deploy` — Admin RBAC deployment of approved candidate.
- `POST /api/models/rollback` — Instant 1-click rollback to previous active model.
- `GET /api/training/status` — Edge node fine-tuning readiness and current run status.
- `POST /api/training/start` — Trigger local fine-tuning run on validated samples.
- `GET /api/training/samples` — List auto-collected and operator-validated samples.
- `POST /api/training/samples/{sample_id}/approve` — Validate sample for local fine-tuning.
- `GET /api/federated/rounds` — List federated learning aggregation rounds.
- `POST /api/federated/rounds` — Create a new multi-edge federated round.
- `POST /api/federated/rounds/{round_id}/aggregate` — Execute sample-weighted FedAvg parameter aggregation.
- `GET /api/federated/privacy` — Privacy telemetry confirming zero raw video transmission.

---

## 10. Master Demo & Simulation Engine (Phase 10)

- `POST /api/demo/master` — Execute the full 10-stage Master End-to-End Demonstration (Parts A through J).
- `POST /api/demo/reset` — Cleanly reset all simulation and demo state across all phases.
- `POST /api/demo/scenario/{1-6}` — Run individual deterministic scenario simulations.

---

## 11. Deterministic State Machine & Jury Readiness (Phase 11)

- `GET /api/demo/status` — Inspect active state machine stage (`DEMO_IDLE` through `DEMO_COMPLETE`), total cameras, and connectivity.
- `POST /api/demo/hero-scenario` — Trigger full 34-step automated hero demonstration run across all 13 stages.
- `POST /api/demo/step/{step_name}` — Execute individual interactive demonstration step (e.g. `1`/`SEE`, `2`/`UNDERSTAND`, `3`/`VERIFY`, `4`/`SUPPRESS`, `5`/`CORRELATE`, `6`/`ASSESS`, `7`/`RESPOND`, `8`/`PROVE`, `9`/`TAMPER`, `10`/`RESTORE`, `11`/`OFFLINE`, `12`/`SYNC`, `13`/`LEARN`).
- `POST /api/demo/reset` — Cleanly reset demo controller state back to Stage 0 (`DEMO_IDLE`).
