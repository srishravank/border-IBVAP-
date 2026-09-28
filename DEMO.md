# IBVAP 2.0 — Final Jury Demonstration Guide

**Project:** IBVAP 2.0 (Intelligent Border Video Analytics & Evidence Platform)  
**Hackathon:** Smart India Hackathon (SIH26187)

---

## 1. Demonstration Philosophy

The final jury demonstration highlights the complete 8-stage operational pipeline:

$$\text{SEE} \to \text{UNDERSTAND} \to \text{VERIFY} \to \text{CORRELATE} \to \text{ASSESS} \to \text{RESPOND} \to \text{PROVE} \to \text{LEARN}$$

Every claim is supported by live sensor telemetry, cryptographic proofs, or measured benchmark gains.

---

## 2. Step-by-Step 10-Part Demonstration Script

### PART A — SEE (CCTV Video Ingestion & Health)
1. Open the dashboard at `http://localhost:5173`.
2. Direct the jury's attention to the **CCTV Matrix & AI** view.
3. Point out live streams across `CAM-01` (Main Gate), `CAM-02` (Perimeter Fence), `CAM-03` (Riverine Crossing), and `CAM-04` (Road Checkpoint).
4. Highlight real-time FPS telemetry and frame health indicators.

---

### PART B — UNDERSTAND (AI Perception & ByteTrack Tracking)
1. Observe bounding boxes, class labels (`person`, `vehicle`), and persistent track IDs (`P017`, `V005`).
2. Show continuous Kalman-filtered trajectory trails indicating heading and speed.

---

### PART C — VERIFY (Virtual Zones & 3-of-5 Temporal Verification)
1. Switch to the **Virtual Zones & Gates** tab.
2. Show custom polygon exclusion strips and perimeter fences drawn over cameras.
3. Explain the Ray-Casting ground-contact check and the 3-of-5 sliding-window temporal gate that rejects transient noise and animal false alarms.

---

### PART D — CORRELATE (Cross-Camera Re-ID & Incident Graph)
1. Navigate to the **Cross-Camera Intel** tab.
2. Observe how the subject moving across `CAM-01` $\to$ `CAM-02` $\to$ `CAM-03` is automatically correlated into a single global entity (`SUBJ-001`).
3. Open the **Topological Incident Graph** modal to show the node-edge representation linking multi-camera observations and contextual vehicles.

---

### PART E — ASSESS (Explainable Risk Engine Radar)
1. Switch to the **Risk Engine Radar** tab.
2. Inspect the threat score ($0–100$) and explainable factor breakdown (Zone Sensitivity, Fence Crossing, Night Period, Trajectory Heading, Contextual Vehicle).
3. Demonstrate the clear separation of concrete sensor **FACT** from analytical **ASSESSMENT**.

---

### PART F — RESPOND (Command & Response Cockpit)
1. Navigate to the **Incident Command** tab.
2. Review real-time alert notifications and the **Sector Risk Map**.
3. Inspect **Recommended Forward-Tracking Cameras** grounded in physical topology adjacency.
4. Execute human-in-the-loop operator actions: **Acknowledge**, **Attach Investigation Note**, and transition to `INVESTIGATING`.

---

### PART G — PROVE (Tamper-Evident Evidence & Blockchain Anchoring)
1. Open the **Forensics & Audit** tab.
2. Click **Generate Evidence Package** for the active incident.
3. Point out the RFC-8785 canonical manifest, calculated SHA-256 hash, and private blockchain block seal.
4. Click **Verify Evidence** $\to$ observe `AUTHENTIC` status.
5. Click **Simulate Tampering** $\to$ observe immediate cryptographic `TAMPERED` detection with detailed diff analysis.
6. Click **Restore Authentic Evidence** $\to$ re-verify status returns to `AUTHENTIC`.

---

### PART H & I — RESILIENCE (Offline Operation & Resilient Sync)
1. Click **Simulate Offline Mode** in the header or via API.
2. Observe that edge AI inference, incident creation, operator actions, and evidence generation continue uninterrupted.
3. Inspect the durable **Sync Queue** holding pending records.
4. Click **Restore Network & Sync** $\to$ observe automatic idempotent synchronization and confirmation of deferred ledger anchors.

---

### PART J — LEARN (On-Device & Federated Learning Hub)
1. Navigate to the **Federated AI & Learn** tab.
2. Emphasize the **Zero Raw Footage Leakage** privacy-by-design guarantee.
3. Show the **8-Stage Governance Lifecycle**: Validated Samples $\to$ Edge Fine-Tuning $\to$ Parameter Deltas $\to$ FedAvg Aggregation $\to$ Candidate Model $\to$ Benchmark Validation Gate (+1.2% mAP gain) $\to$ Supervisor Approval $\to$ Safe Deployment.
4. Demonstrate **1-Click Instant Rollback** returning to the previous baseline model with full audit provenance.

---

## 3. Automated Single-Click Master Demo

To execute the entire 10-part pipeline in an automated sequence, click **Run Phase 9/10 Master Demo** in the UI or call:

```bash
curl -X POST http://localhost:8000/api/demo/master
```
