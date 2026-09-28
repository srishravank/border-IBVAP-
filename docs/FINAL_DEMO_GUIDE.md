# IBVAP 2.0 — Final Demo & Jury Presentation Script

## 1. Executive Summary & Value Proposition (1 Minute)

> *"Distinguished Jury Members: Modern border surveillance suffers from three critical failure points: bandwidth bottlenecks over remote links, overwhelming false-alarm fatigue for operators, and legal vulnerability of digital video evidence to tampering. **IBVAP 2.0** solves all three by providing an autonomous Edge AI architecture that sees, verifies, tracks cross-camera, calculates explainable risk, cryptographically anchors evidence, functions 100% offline, and continuously learns via federated models without transmitting raw video."*

---

## 2. Interactive 13-Stage Demo Flow (4 to 5 Minutes)

You can run this demo interactively step-by-step from the **Simulation Lab** in the frontend, or trigger the automated Hero Scenario runner.

```
[1. SEE] ──> [2. UNDERSTAND] ──> [3. VERIFY] ──> [4. SUPPRESS] ──> [5. CORRELATE]
                                                                        │
[10. RESTORE] <── [9. TAMPER] <── [8. PROVE] <── [7. RESPOND] <── [6. ASSESS]
      │
[11. OFFLINE] ──> [12. SYNC] ──> [13. LEARN] (Continuous On-Device Adaptation)
```

---

### Phase I: Detection & False-Positive Elimination (Stages 1–4)

#### Stage 1: SEE — Multi-Camera Edge Ingestion
- **Action**: In UI Simulation Lab, click **Stage 1: SEE** (or `POST /api/demo/step/1`).
- **Narrative**: *"Our pipeline ingests 4 synchronized RTSP edge feeds across Sector Alpha. In production, this runs on local edge hardware at ~47ms per frame."*
- **Visuals**: Live 4-camera matrix (CAM-01 North Fence, CAM-02 Buffer Zone, CAM-03 Infiltration Path, CAM-04 Outpost Gate).

#### Stage 2: UNDERSTAND — Neural Detection & ByteTrack
- **Action**: Click **Stage 2: UNDERSTAND**.
- **Narrative**: *"YOLOv8n classifies targets in real-time while ByteTrack maintains persistent subject trajectories across camera occlusions."*
- **Visuals**: Bounding boxes with tracking IDs (`#101 [Person]`, `#102 [Vehicle]`).

#### Stage 3: VERIFY — Dual-Verification Gating
- **Action**: Click **Stage 3: VERIFY**.
- **Narrative**: *"Targets entering restricted zones trigger mathematical dwell filters and polygon cross-checks before any alarm is raised."*
- **Visuals**: Zone polygon breach indicator turns from yellow to amber.

#### Stage 4: SUPPRESS — False Alarm Elimination
- **Action**: Click **Stage 4: SUPPRESS**.
- **Narrative**: *"Environmental noise, swaying trees, and wildlife are suppressed using spatial-temporal motion validation, eliminating >94% of false alarms."*
- **Visuals**: Suppression breakdown card shows environmental noise filtered.

---

### Phase II: Intelligence & Tactical Response (Stages 5–7)

#### Stage 5: CORRELATE — Multi-Camera Re-ID & Journey Graph
- **Action**: Click **Stage 5: CORRELATE**.
- **Narrative**: *"As the target moves from CAM-01 to CAM-02 and CAM-03, IBVAP constructs an unified spatial-temporal journey graph."*
- **Visuals**: Incident graph modal showing connected nodes across 3 cameras with transition timestamps.

#### Stage 6: ASSESS — Explainable Risk Engine
- **Action**: Click **Stage 6: ASSESS**.
- **Narrative**: *"IBVAP computes a composite risk score of 85/100 (HIGH RISK) with clear, auditable factors: Zone Severity (95), Dwell Time (80), Night-time Vectoring (88)."*
- **Visuals**: Risk gauge dial and explainability breakdown bars.

#### Stage 7: RESPOND — Command & Dispatch Workflows
- **Action**: Click **Stage 7: RESPOND**.
- **Narrative**: *"Operators receive tailored SOP checklists, automated PTZ camera tracking lock, and one-click field unit dispatch."*
- **Visuals**: Operator response matrix logs dispatch of Unit Alpha-4.

---

### Phase III: Evidence Trust & Tamper Demonstration (Stages 8–10)

#### Stage 8: PROVE — SHA-256 Cryptographic Anchoring
- **Action**: Click **Stage 8: PROVE**.
- **Narrative**: *"The system freezes all incident telemetry, trajectory nodes, and operator actions into an immutable Evidence Manifest anchored with SHA-256."*
- **Visuals**: Evidence Trust Vault shows green `INTEGRITY VERIFIED` badge and SHA-256 hash.

#### Stage 9: TAMPER — Live Tampering Simulation
- **Action**: Click **Stage 9: TAMPER**.
- **Narrative**: *"Let's simulate a hostile actor attempting to modify the evidence timestamps or delete incident logs directly in the database."*
- **Visuals**: Vault integrity badge immediately flips to flashing red `TAMPER DETECTED: HASH MISMATCH`.

#### Stage 10: RESTORE — Cryptographic State Recovery
- **Action**: Click **Stage 10: RESTORE**.
- **Narrative**: *"The system detects the hash mismatch and automatically restores genuine evidence records from the anchored consensus root."*
- **Visuals**: Badge returns to green `RESTORED & VALIDATED`.

---

### Phase IV: Resilience & Continuous Learning (Stages 11–13)

#### Stage 11: OFFLINE — Severed Network Survival
- **Action**: Click **Stage 11: OFFLINE**.
- **Narrative**: *"Remote border posts frequently lose connectivity. We sever the uplink now — the edge node continues detection, tracking, and risk logging to local WAL storage without missing a single frame."*
- **Visuals**: Top header displays amber `OFFLINE - QUEUING (WAL ACTIVE)`.

#### Stage 12: SYNC — Zero-Loss Resilient Reconnection
- **Action**: Click **Stage 12: SYNC**.
- **Narrative**: *"Satellite link is restored. The priority queue immediately drains 100% of buffered events in priority order with zero record duplication."*
- **Visuals**: Header flips back to green `ONLINE`, Sync Queue drains to 0 pending.

#### Stage 13: LEARN — Privacy-Preserving Federated Adaptation
- **Action**: Click **Stage 13: LEARN**.
- **Narrative**: *"Edge models continuously improve on local terrain. Without transmitting private video footage, model gradients are aggregated via FedAvg into global weights."*
- **Visuals**: Federated Learning card shows Round completed, accuracy gain (+4.2%), and updated model hash.

---

## 3. Automated One-Click Hero Scenario Demo

If you prefer an automated continuous run:
1. Open **Simulation Lab**.
2. Click **"Run Hero Scenario (All 13 Stages)"** button.
3. The platform executes all 13 stages automatically with real-time logs and progress meters.
4. Click **"Reset System State"** at the conclusion to reset for the next presentation.
