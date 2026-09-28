# IBVAP 2.0 — System Architecture & Data Flow

## 1. Architectural Principles

IBVAP 2.0 is built around an 11-stage design pipeline:

$$\text{SEE} \longrightarrow \text{UNDERSTAND} \longrightarrow \text{VERIFY} \longrightarrow \text{CORRELATE} \longrightarrow \text{ASSESS} \longrightarrow \text{RESPOND} \longrightarrow \text{PROVE} \longrightarrow \text{RESILIENCE} \longrightarrow \text{LEARN} \longrightarrow \text{INTEGRATION} \longrightarrow \text{READINESS}$$

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          IBVAP 2.0 DATA PIPELINE                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
[1. SEE]           CCTV / RTSP / Video Stream Ingestion (CameraManager)
                                      │
                                      ▼ (Frame Buffer)
[2. UNDERSTAND]    YOLOv8 / RT-DETR + ByteTrack Tracking (AIPipelineService)
                                      │
                                      ▼ (Tracked Observations)
[3. VERIFY]        Ray-Casting Polygon Check & 3/5 Verification Gate (EventManager)
                                      │
                                      ▼ (Confirmed Security Events)
[4. CORRELATE]     Spatiotemporal Re-ID & Incident Graph (CrossCameraEngine)
                                      │
                                      ▼ (Unified Incident Entity)
[5. ASSESS]        Multi-Factor Weighted Risk Scoring & Explainability (RiskService)
                                      │
                                      ▼ (Risk Assessments & Alerts)
[6. RESPOND]       SOC Command Center, Forward Cameras & Operator Actions (CommandService)
                                      │
                                      ▼ (Incident Lifecycle & Actions)
[7. PROVE]         RFC-8785 Canonical Manifest, SHA-256 & Private Ledger (EvidenceService)
                                      │
                                      ▼ (Cryptographically Sealed Evidence)
[8. RESILIENCE]    Offline-First Priority Queue & Idempotent Sync (SyncService)
                                      │
                                      ▼ (Synchronized Telemetry)
[9. LEARN]         Privacy-Preserving Edge Fine-Tuning & FedAvg Aggregation (FederatedService)
                                      │
                                      ▼ (Candidate Benchmark -> Human Approval -> Safe Deploy)
[10. INTEGRATION]  Full System Hardening & End-to-End Orchestration (SimulationEngine)
                                      │
                                      ▼ (Deterministic 13-Stage Demo Controller & Jury Mode)
[11. READINESS]    Benchmark Validation, Demo Simulation & Jury Readiness (DemoController)
```

---

## 2. Layer Specifications

### Phase 1: SEE — Ingestion & Video Health
- **Components:** `CameraManager`, `VideoSource` (File, RTSP, Webcam), `CameraHealthMonitor`.
- **Function:** Ingests live streams at steady FPS, enforces zero-copy frame hooks, and monitors for frozen, degraded, or black frames.

### Phase 2: UNDERSTAND — AI Perception & Tracking
- **Components:** `YOLODetector`, `RTDETRDetector`, `ByteTrackTracker`, `KalmanFilter`.
- **Function:** Identifies persons and vehicles, maintains Kalman state estimations, and tracks continuous trajectories across frame boundaries.

### Phase 3: VERIFY — Virtual Zones & False-Positive Suppression
- **Components:** `PolygonEngine`, `TemporalVerificationGate`, `FalsePositiveFilter`.
- **Function:** Tests ground-contact reference points against arbitrary polygon boundaries using ray-casting. Requires 3 of 5 sliding-window frame confirmations to eliminate transient sensor noise and animal false alarms (>94% suppression).

### Phase 4: CORRELATE — Cross-Camera Intelligence & Incident Graph
- **Components:** `AppearanceMatcher`, `TemporalMatcher`, `TrajectoryMatcher`, `TopologyService`, `IncidentGraphBuilder`.
- **Function:** Probabilistic multi-factor Re-ID combining physical topology adjacency, travel transit windows, heading trajectories, and color histograms to assign persistent global subject IDs and construct incident graphs.

### Phase 5: ASSESS — Explainable Risk Engine
- **Components:** `RiskAggregator`, `ExplanationGenerator`, 7 Discrete Factor Evaluators (`Zone`, `Fence`, `Night`, `Trajectory`, `CrossCamera`, `Vehicle`, `Behaviour`).
- **Function:** Computes normalized 0–100 threat scores, categorizes into discrete tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and generates natural language explanations.

### Phase 6: RESPOND — Command & Response
- **Components:** `CommandService`, `IncidentCommandView`, `IncidentInvestigationModal`.
- **Function:** Human-in-the-loop operator workstation with real-time alert ticker, sector risk map, topology forward-tracking camera recommendations, and collaborative note-taking.

### Phase 7: PROVE — Evidence Trust & Blockchain Anchoring
- **Components:** `EvidenceService`, `EvidenceHashService`, `LedgerService`.
- **Function:** Assembles court-admissible evidence manifests, canonicalizes via RFC-8785, computes SHA-256 hashes, and anchors to an immutable private blockchain. Detects unauthorized retroactive alterations in real time.

### Phase 8: RESILIENCE — Offline-First Operation & Resilient Sync
- **Components:** `ConnectivityService`, `SyncService`, `CentralSyncReceiver`.
- **Function:** Allows edge nodes to operate autonomously during network disruptions with priority-based SQLite queueing, exponential backoff retries, and idempotent deduplication upon reconnection.

### Phase 9: LEARN — On-Device & Federated Learning
- **Components:** `TrainingSampleService`, `LocalTrainingService`, `FederatedAggregator`, `ModelRegistryService`.
- **Function:** Privacy-preserving edge fine-tuning with zero raw surveillance video transmission. Enforces controlled candidate validation gates, supervisor RBAC approval, and 1-click rollback.

### Phase 10: INTEGRATION — Full System Hardening
- **Components:** `simulation_engine.run_master_e2e_demo()`, unified health check (`/api/system/health`), comprehensive regression test suite.

### Phase 11: READINESS — Final Validation, Demo Simulation & Jury Readiness
- **Components:** `DemoController`, `DemoStage` (13 stages), `/api/demo/*` REST endpoints, Jury Mode UI toggle, automated Hero Scenario runner.
- **Function:** Provides deterministic, repeatable live presentation controls, measured performance benchmarks, and jury defense documentation.

---

## 3. Global Entity Identifiers

| Entity | Identifier Format | Example |
| :--- | :--- | :--- |
| **Camera** | `CAM-<NUM>` | `CAM-01`, `CAM-SECTOR-A1` |
| **Track** | `P<NUM>` / `V<NUM>` | `P017`, `V005` |
| **Security Event** | `EVT-<NAME>-<NUM>` | `EVT-DEMO-001` |
| **Global Subject** | `SUBJ-<NUM>` / `VEH-<NUM>` | `SUBJ-001`, `VEH-001` |
| **Incident** | `INC-<SUBJECT_ID>` | `INC-SUBJ-001` |
| **Operator Action** | `ACT-<TYPE>-<ID>` | `ACT-ACK-INC-SUBJ-001` |
| **Evidence Package** | `EVD-<INCIDENT_ID>-<VER>` | `EVD-INC-SUBJ-001-v1.0` |
| **Blockchain Block** | `BLOCK-<NUM>` | `BLOCK-0001` |
| **Sync Item** | `SYNC-<TIMESTAMP>-<ID>` | `SYNC-1726912345-A1B2` |
| **AI Model Version** | `MODEL-<ARCH>-V<VER>` | `MODEL-YOLO-V1.0.0` |
| **Training Run** | `RUN-<EDGE_ID>-<ID>` | `RUN-EDGE-SECTOR-A-01-F3A1` |
| **Federated Round** | `ROUND-<NUM>` | `ROUND-001` |
