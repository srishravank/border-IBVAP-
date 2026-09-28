# IBVAP 2.0 — Intelligent Border Video Analytics & Evidence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18.2.0-cyan.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests Passing](https://img.shields.io/badge/tests-135%2F135%20passed-brightgreen.svg)](tests/)

> **Smart India Hackathon (SIH26187)**  
> *An Edge-First, Multi-Camera, Explainable AI, Cryptographically Anchored & Privacy-Preserving Border Security Operating System.*

---

## 📑 Table of Contents

- [System Overview](#-system-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Directory Structure](#-directory-structure)
- [Prerequisites](#-prerequisites)
- [Step-by-Step Quickstart Guide](#-step-by-step-quickstart-guide)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Configure Environment Variables](#2-configure-environment-variables)
  - [3. Backend Setup & Dependencies](#3-backend-setup--dependencies)
  - [4. Generate Simulated Video Feeds & Models](#4-generate-simulated-video-feeds--models)
  - [5. Frontend Setup & Dependencies](#5-frontend-setup--dependencies)
  - [6. Launch the Platform](#6-launch-the-platform)
- [Running Automated Tests](#-running-automated-tests)
- [Running the Interactive Demo / Simulation](#-running-the-interactive-demo--simulation)
- [API & Service Endpoints](#-api--service-endpoints)
- [Documentation Index](#-documentation-index)
- [Troubleshooting & FAQs](#-troubleshooting--faqs)

---

## 🛡️ System Overview

**IBVAP 2.0** is an edge-first surveillance operating system designed for multi-camera border sectors (CCTV, RTSP, Thermal, Night-Vision). It detects, tracks, verifies, and correlates potential border anomalies with explainable AI reasoning while ensuring chain-of-custody cryptographic evidence trust and federated edge learning.

### The 11-Phase Workflow:
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
READINESS    ──>  Phase 11: Final Benchmark Validation, Demo Simulation & Jury Readiness
```

---

## ✨ Key Features

- 🔒 **Privacy-by-Design:** Raw video footage stays on the edge device. Only model gradients ($\Delta W$), tamper hashes, and aggregated metadata are shared centrally.
- 🧠 **Explainable Threat Scoring:** Every threat calculation (0–100) breaks down into deterministic sub-factors with full attribution (sensor facts vs. threat deductions).
- ⛓️ **Cryptographic Chain of Custody:** Evidence manifests are normalized, SHA-256 hashed, and anchored to a local tamper-evident blockchain ledger. Real-time tampering is immediately flagged.
- 📡 **Offline-First Fault Tolerance:** Operates completely offline during communication dropouts using SQLite WAL queues, auto-reconciling when back online.
- 🤝 **Human-in-the-Loop AI Governance:** No autonomous lethal actions. Model updates require evaluation gates and one-click rollback.
- 🕹️ **Built-in 13-Stage Demo Machine:** One-click simulation lab and automated hero scenarios for reliable live demonstrations.

---

## 🏗️ Directory Structure

```text
border-IBVAP-/
├── ai/                     # AI Pipeline (detection, tracking, preprocessing, schemas)
├── backend/                # FastAPI Application
│   ├── api/                # REST & WebSocket API Routers (cameras, zones, risk, sync, etc.)
│   ├── database/           # SQLite / SQLAlchemy Models & Connection
│   ├── health/             # Camera & Stream Health Monitoring
│   ├── models/             # Pydantic Schemas & Data Transfer Objects
│   ├── services/           # Core Domain Services (Risk Engine, Evidence, Sync, Ledger)
│   └── main.py             # FastAPI Application Entry Point
├── data/
│   └── videos/             # Video Streams / Synthetic Test Feeds (.mp4)
├── docs/                   # Full Technical Documentation, Guides & Checklists
├── frontend/               # React 18 + Vite + Tailwind CSS SOC Operator Dashboard
│   ├── src/                # UI Components, Views, State, and API Services
│   └── package.json        # Frontend Dependencies & Scripts
├── intelligence/           # Risk Assessment, Graph Models, Cross-Camera Matching
├── scripts/                # Utility & Simulation Scripts (e.g. Video Generator)
├── storage/                # Evidence & Audit Artifacts (ignored by git)
├── tests/                  # Automated Test Suite (135+ tests)
├── verification/           # Temporal Gating & False Positive Suppression
├── .env.example            # Sample Environment Configuration
├── .gitignore              # Repository Git Ignore Rules
├── requirements.txt        # Python Dependencies
└── README.md               # Main Project Readme
```

---

## ⚙️ Prerequisites

Before installing, ensure your machine has the following:

- **Python:** `3.10` or higher (3.11/3.12 recommended)
- **Node.js:** `v18.0.0` or higher & **npm** `v9.0.0` or higher
- **Git:** Installed and available in your `PATH`
- **C++ Build Tools / FFmpeg (Optional):** Required only if compiling OpenCV from source or using hardware-accelerated video codecs.

---

## 🚀 Step-by-Step Quickstart Guide

### 1. Clone the Repository

```bash
git clone https://github.com/srishravank/border-IBVAP-.git
cd border-IBVAP-
```

### 2. Configure Environment Variables

Copy the provided `.env.example` file to create your `.env` configuration:

**Linux / macOS:**
```bash
cp .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Windows (CMD):**
```cmd
copy .env.example .env
```

*(Optional)* Modify `.env` to adjust camera stream ports, database paths, or threshold values as needed.

---

### 3. Backend Setup & Dependencies

It is strongly recommended to use a Python virtual environment:

#### Create & Activate Virtual Environment:
- **Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- **Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (CMD):**
  ```cmd
  python -m venv venv
  venv\Scripts\activate.bat
  ```

#### Install Python Dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 4. Generate Simulated Video Feeds & Models

To run the camera pipelines and simulation lab without connecting physical RTSP cameras, generate synthetic multi-sector CCTV feeds:

```bash
python scripts/generate_sample_videos.py
```
> This creates 4 synthetic camera feeds (`camera01.mp4` to `camera04.mp4`) under `data/videos/` simulating gate, perimeter, riverine, and watchtower sectors.

*Note: The YOLOv8 model (`yolov8n.pt`) will automatically download on first run via Ultralytics when the detector initializes.*

---

### 5. Frontend Setup & Dependencies

Open a new terminal window to configure the React SOC operator interface:

```bash
cd frontend
npm install
```

---

### 6. Launch the Platform

#### Terminal 1 — Start the Backend Server:
```bash
# From the repository root with virtual environment activated:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- **API Server:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **System Health Check:** `http://localhost:8000/api/system/health`

#### Terminal 2 — Start the Frontend Dashboard:
```bash
cd frontend
npm run dev
```
- **SOC Command Center Dashboard:** `http://localhost:5173`

---

## 🧪 Running Automated Tests

IBVAP 2.0 includes a comprehensive test suite with 135+ tests covering AI pipelines, ByteTrack tracking, polygon ray-casting, risk calculation, evidence hashing, blockchain ledgers, and federated learning:

```bash
# Run the complete test suite
pytest -v

# Run with test coverage report
pytest --cov=backend --cov=intelligence --cov=verification
```

---

## 🎮 Running the Interactive Demo / Simulation

You can experience the 13-stage security incident lifecycle through either the Web UI or the REST API:

### Option A: Via Web UI
1. Navigate to `http://localhost:5173`.
2. Click on **Simulation Lab** in the navigation bar.
3. Use the **Hero Scenario** button or step through the 13 interactive stages.

### Option B: Via Terminal / cURL
```bash
# Trigger the complete End-to-End Hero Scenario
curl -X POST http://localhost:8000/api/demo/hero-scenario

# Check the current stage of the state machine
curl http://localhost:8000/api/demo/status
```

---

## 🔌 API & Service Endpoints

| Category | Route | Description |
| :--- | :--- | :--- |
| **System** | `GET /api/system/health` | Unified health across edge ingestors, DB, and AI pipelines |
| **Cameras** | `GET /api/cameras` | List all active camera streams and health metrics |
| **Zones** | `POST /api/zones` | Configure polygon virtual zones & intrusion rules |
| **Incidents** | `GET /api/incidents` | Query active security incidents and risk levels |
| **Risk Engine** | `POST /api/risk/assess` | Request real-time explainable risk assessment |
| **Evidence** | `GET /api/evidence/{id}` | Inspect evidence package manifest & hash proof |
| **Ledger** | `POST /api/evidence/verify` | Verify evidence integrity against private blockchain |
| **Learning** | `POST /api/learning/round` | Initiate privacy-preserving federated aggregation |
| **Simulation** | `POST /api/demo/hero-scenario` | Execute 13-stage live jury demonstration |
| **WebSocket** | `WS /ws/live` | Real-time multi-camera frame telemetry and alerts |

---

## 📚 Documentation Index

For in-depth explanations, refer to the guides in the repository:

- 📖 [ARCHITECTURE.md](ARCHITECTURE.md) — Comprehensive layer-by-layer architectural blueprint.
- 📡 [API.md](API.md) — Full REST and WebSocket API specification.
- 🎯 [docs/FINAL_DEMO_GUIDE.md](docs/FINAL_DEMO_GUIDE.md) — Step-by-step hackathon presentation script.
- ⚖️ [docs/JURY_EXPLANATION_GUIDE.md](docs/JURY_EXPLANATION_GUIDE.md) — Architectural defense & technical Q&A.
- 📊 [docs/performance_report.md](docs/performance_report.md) — Hardware performance and latency profiles.
- 🛠️ [docs/DEMO_CHECKLIST.md](docs/DEMO_CHECKLIST.md) — Pre-presentation operational verification checklist.
- 🚀 [DEPLOYMENT.md](DEPLOYMENT.md) — Production edge deployment and containerization guide.
- 🔧 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Diagnostics and common resolution steps.

---

## ❓ Troubleshooting & FAQs

<details>
<summary><b>1. ModuleNotFoundError: No module named 'backend' / 'intelligence'</b></summary>
Ensure you are running commands from the <b>root directory</b> of the repository and that your virtual environment is active. You can also run:
```bash
# On Linux/macOS:
export PYTHONPATH=.
# On Windows PowerShell:
$env:PYTHONPATH="."
```
</details>

<details>
<summary><b>2. OpenCV video read error or missing data/videos/ files</b></summary>
Run the synthetic video generator script:
```bash
python scripts/generate_sample_videos.py
```
This generates standard MP4 sample video files for all 4 camera channels.
</details>

<details>
<summary><b>3. Port 8000 or 5173 already in use</b></summary>
- Backend port can be changed in `.env` or via CLI: `python -m uvicorn backend.main:app --port 8080 --reload`
- Frontend port can be specified with: `npm run dev -- --port 3000`
</details>

<details>
<summary><b>4. How to connect physical RTSP / USB Webcam streams?</b></summary>
Use the <b>Add Camera Modal</b> in the frontend or post to `/api/cameras` with `source_type: "rtsp"` and the RTSP URL (e.g., `rtsp://user:pass@192.168.1.50:554/stream1`), or `source_type: "webcam"` with camera index `0`.
</details>

---

## 👥 Contributors

- **Team Smart India Hackathon (SIH26187)**
- Repository: [srishravank/border-IBVAP-](https://github.com/srishravank/border-IBVAP-)
