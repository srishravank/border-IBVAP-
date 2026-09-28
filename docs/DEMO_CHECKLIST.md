# IBVAP 2.0 — Pre-Demo Checklist & Presentation Verification

## 1. System Environment Verification

- [x] **Backend Python Environment**: Python 3.12+ with PyTorch, Ultralytics, FastAPI, Uvicorn, SQLAlchemy.
- [x] **Frontend Environment**: Node.js 18+, Vite, React 18, TailwindCSS.
- [x] **Local Database**: SQLite with WAL mode (`ibvap.db`) initialized and migrated.
- [x] **AI Model Weights**: `yolov8n.pt` downloaded and verified locally in project root.
- [x] **Test Suite**: 135+ automated tests passing with zero failures.

---

## 2. Pre-Presentation Setup Steps

1. **Start Backend Server**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *Verify health*: Open `http://localhost:8000/api/health` or `http://localhost:8000/docs`.

2. **Start Frontend Client**:
   ```bash
   cd frontend
   npm run dev
   ```
   *Verify UI*: Open `http://localhost:5173` in a modern browser (Chrome / Edge).

3. **Reset System State to Clean Baseline**:
   - In UI: Navigate to **Simulation Lab** tab, click **"Reset System State"** button (or send `POST /api/demo/reset`).
   - Confirm active stage shows `IDLE` (Step 0/13).

4. **Enable Jury Mode (Optional / Recommended)**:
   - Click the **"Jury Mode"** badge in the top-right header to activate high-visibility indicator banners and simplified operator views.

---

## 3. Presentation Flow Verification

| Step | Stage | Target UI Screen | Key Action / Indicator | Expected Outcome |
| :---: | :---: | :---: | :---: | :---: |
| 1 | **SEE** | Live Camera Grid | Click Step 1 or "Start Simulation" | 4 CCTV feeds render active bounding boxes & FPS |
| 2 | **UNDERSTAND** | Detection Overlay | Click Step 2 | Detections classify Person/Vehicle with tracking IDs |
| 3 | **VERIFY** | Verification Panel | Click Step 3 | Crossing triggers spatial & dwell verification gate |
| 4 | **SUPPRESS** | False Positive Tab | Click Step 4 | Animal / tree noise filtered (>94% suppression) |
| 5 | **CORRELATE** | Incident Graph | Click Step 5 | Multi-camera journey links CAM-01 to CAM-02/03 |
| 6 | **ASSESS** | Risk Breakdown Card | Click Step 6 | Risk score calculated (e.g., 85/100 HIGH RISK) |
| 7 | **RESPOND** | Tactical Response Matrix | Click Step 7 | SOP checklists, PTZ lock, unit dispatch logged |
| 8 | **PROVE** | Evidence Trust Vault | Click Step 8 | Evidence bundle generated with SHA-256 & anchor |
| 9 | **TAMPER** | Evidence Vault | Click Step 9 | Simulated tampering flips badge to `TAMPER DETECTED` |
| 10 | **RESTORE** | Evidence Vault | Click Step 10 | Restore action recovers state, badge turns `VALID` |
| 11 | **OFFLINE** | Connectivity Banner | Click Step 11 | Simulated link loss shows `OFFLINE - QUEUING` |
| 12 | **SYNC** | Sync Queue View | Click Step 12 | Link restored, queue drains 100% with zero loss |
| 13 | **LEARN** | Federated Learning Lab | Click Step 13 | Local training gradients aggregated via FedAvg |

---

## 4. Fallback & Troubleshooting Procedures

- **If Video Feed fails or lags**:
  - The system automatically serves synthetic procedural canvas fallback frames with simulated detections and bounding boxes.
- **If Port 8000 is occupied**:
  - Run `uvicorn backend.main:app --port 8001` and set `VITE_API_URL=http://localhost:8001` in frontend.
- **If Demo State becomes desynchronized**:
  - Click **"Reset System State"** at any point in the Simulation Lab to return to Stage 0 cleanly without restarting the server.
