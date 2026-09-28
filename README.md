# IBVAP 2.0 — Intelligent Border Video Analytics & Evidence Platform
**Smart India Hackathon (SIH26187) — Release Candidate 1 (v1.0.0-rc1)**  
*An Edge-First, Multi-Camera, Explainable AI, Cryptographically Anchored & Privacy-Preserving Border Security Operating System.*

---

## 1. System Overview

IBVAP 2.0 is a production-grade border security platform designed to detect, track, verify, correlate, assess, manage, prove, and learn from physical security events across heterogeneous camera networks (CCTV, RTSP, Thermal, Night-Vision).

### The Complete 11-Phase Architecture
```
SEE          ──>  Phase 1: Multi-Camera Edge CCTV / RTSP / File Video Ingestion & Health
UNDERSTAND   ──>  Phase 2: YOLOv8 / RT-DETR Detection & ByteTrack Multi-Object Tracking
VERIFY       ──>  Phase 3: Polygon Virtual Zones, Ray-Casting & 3-of-5 Temporal Verification
CORRELATE    ──>  Phase 4: Spatiotemporal Cross-Camera Re-ID & Topological Incident Graph
ASSESS       ──>  Phase 5: Multi-Factor Weighted Explainable Risk Engine (0-100 Score)
RESPOND      ──>  Phase 6: SOC Command Center, Adjacency Forward-Tracking & Human RBAC
PROVE        ──>  Phase 7: Tamper-Evident Evidence Package, SHA-256 & Private Blockchain Ledger
RESILIENCE   ──>  Phase 8: Offline-First Edge Operation, Resilient Queue & Idempotent Sync
LEARN        ──>  Phase 9: Privacy-Preserving On-Device Fine-Tuning & FedAvg Federated Aggregation
HARDENING    ──>  Phase 10: Full End-to-End Integration, Unified Health & Master Demonstration
READINESS    ──>  Phase 11: Final Benchmark Validation, Demo Simulation & Jury Readiness (RC1)
```

---

## 2. Key Capabilities & Architectural Guarantees

- **Privacy by Design:** Raw surveillance video and full-resolution images **never leave the edge node**. Only model weight gradients ($\Delta W$), metrics, and SHA-256 hashes are exchanged with central systems.
- **Zero Black-Box Reasoning:** Every threat score includes a deterministic, explainable factor breakdown with clear separation of sensor **FACT** from analytical **ASSESSMENT**.
- **Human-in-the-Loop Governance:** AI never executes autonomous operational interventions. Models require multi-stage benchmark validation, supervisor approval, and feature 1-click instant rollback.
- **Court-Admissible Evidence Trust:** Incident evidence manifests are canonicalized and hashed via SHA-256, then permanently anchored to a private blockchain ledger. Tampering is cryptographically detected in real time.
- **Offline-First Resilience:** In the event of network disruption, edge AI detection, tracking, verification, risk assessment, and evidence packaging continue locally without data loss.
- **Deterministic 13-Stage Demo Machine & Jury Mode:** Built-in interactive state machine and one-click Hero Scenario runner for high-reliability live jury evaluation.

---

## 3. Technology Stack & Measured Benchmarks

| Layer | Technologies | Measured Average Latency / Rate |
| :--- | :--- | :--- |
| **Detection (YOLOv8n)** | PyTorch / TorchScript, CLAHE preprocessor | **46.96 ms** (~21.3 FPS on CPU) |
| **Tracking (ByteTrack)** | Kalman Filter, Hungarian Re-ID | **0.14 ms** (>7,000 FPS) |
| **Risk Intelligence** | NetworkX Graph, Multi-Factor Aggregator | **24.58 ms** / incident |
| **Evidence & SHA-256** | Canonical JSON, Merkle Ledger Anchor | **113.06 ms** (Hash Verif: 43.35 ms) |
| **Offline Sync Queue** | SQLite WAL, Resilient Backoff Queue | **83.44 ms** flush cycle |
| **Federated Learning** | FedAvg Protocol, Weight Differential Aggregator | **51.85 ms** / aggregation round |
| **Backend & API** | Python 3.12, FastAPI, Uvicorn, WebSockets | < 5 ms REST overhead |
| **Frontend SOC Cockpit** | React 18, TypeScript, Vite, Tailwind CSS | 60 FPS Tactical Dashboard |
| **Automated Testing** | Pytest (135/135 Tests Passing) | **100% Pass Rate** |

---

## 4. Quick Start & Setup Guide

### Step 1: Start Backend API
```bash
# In the repository root:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- **Backend API:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **Unified Health Endpoint:** `http://localhost:8000/api/system/health`
- **Demo State Machine Status:** `http://localhost:8000/api/demo/status`

### Step 2: Start Frontend SOC Dashboard
```bash
# In a new terminal:
cd frontend
npm install
npm run dev
```
- **Operator Command Center:** `http://localhost:5173`

### Step 3: Run Full Test Suite
```bash
pytest -v
```
*Executes all 135 automated unit, integration, and end-to-end tests with 100% pass rate.*

---

## 5. Master Jury Demonstration Flow

You can run the interactive 13-stage state machine from the **Simulation Lab** in the frontend, or trigger the automated Hero Scenario runner via REST API:

```bash
curl -X POST http://localhost:8000/api/demo/hero-scenario
```

### 13 Interactive Demo Stages:
1. **1. SEE:** Ingestion active across `CAM-01`, `CAM-02`, `CAM-03`, `CAM-04`.
2. **2. UNDERSTAND:** Person & vehicle detection with persistent ByteTrack track IDs.
3. **3. VERIFY:** Restricted zone entry passed through 3-of-5 temporal gate.
4. **4. SUPPRESS:** Environmental noise and false alarms eliminated (>94% suppression).
5. **5. CORRELATE:** Cross-camera Re-ID tracks subject traversing `CAM-01` $\to$ `CAM-02` $\to$ `CAM-03`.
6. **6. ASSESS:** Explainable risk engine generates composite score (85/100) and factor breakdown.
7. **7. RESPOND:** Command Center alert generated; forward-tracking camera recommendation displayed.
8. **8. PROVE:** Evidence package compiled, SHA-256 hashed, and anchored to private blockchain ledger (`AUTHENTIC`).
9. **9. TAMPER:** Simulated tampering immediately triggers red `TAMPER DETECTED: HASH MISMATCH`.
10. **10. RESTORE:** Consensus recovery restores authentic records (`RESTORED & VALIDATED`).
11. **11. OFFLINE:** Network loss simulated; AI processing and operator actions queue locally.
12. **12. SYNC:** Network restored; resumable sync reconciles queued items with zero duplicates.
13. **13. LEARN:** Validated local samples trigger edge fine-tuning, FedAvg aggregation generates candidate model with 1-click rollback.

---

## 6. Project Documentation Index

- [docs/FINAL_DEMO_GUIDE.md](docs/FINAL_DEMO_GUIDE.md): Complete step-by-step hackathon presentation script.
- [docs/JURY_EXPLANATION_GUIDE.md](docs/JURY_EXPLANATION_GUIDE.md): Architecture defense & jury Q&A.
- [docs/performance_report.md](docs/performance_report.md): Measured hardware benchmarks and latency profiles.
- [docs/DEMO_CHECKLIST.md](docs/DEMO_CHECKLIST.md): Pre-presentation operational verification checklist.
- [ARCHITECTURE.md](ARCHITECTURE.md): Full layer-by-layer architectural blueprint.
- [API.md](API.md): Comprehensive REST & WebSocket API specification.
