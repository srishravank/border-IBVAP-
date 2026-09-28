# IBVAP 2.0 — Deployment & Configuration Guide

## 1. System Requirements

### Hardware Requirements
- **Edge Deployment (Outpost Node):**
  - CPU: 4+ Cores (Intel Core i5/i7/Xeon or AMD Ryzen 5/7)
  - RAM: 8 GB Minimum (16 GB Recommended)
  - Storage: 64 GB SSD / NVMe (for offline evidence buffer)
  - GPU (Optional): NVIDIA Jetson Orin, RTX 3060/4060 or CPU inference fallback
- **Central Command Post:**
  - CPU: 8+ Cores
  - RAM: 16 GB+
  - Storage: 256 GB+ SSD

### Operating Systems Supported
- Windows 10 / 11 / Windows Server
- Ubuntu Linux 20.04 / 22.04 LTS
- Debian 11 / 12

---

## 2. Environment Configuration (`.env`)

Create or update `.env` in the root directory:

```ini
# Core Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
DATABASE_URL=sqlite:///./ibvap.db

# Edge Node Identity
EDGE_ID=EDGE-SECTOR-A-01

# AI Perception & Detection
AI_ENABLED=true
AI_DETECTOR_TYPE=yolo
AI_MODEL_PATH=yolov8n.pt
AI_DEVICE=auto
DETECTION_CONFIDENCE=0.35
IOU_THRESHOLD=0.45

# Verification & Spatial Parameters
ZONE_ENABLED=true
VERIFICATION_REQUIRED_FRAMES=3
VERIFICATION_WINDOW_FRAMES=5

# Cross-Camera Intelligence
CROSS_CAMERA_MATCH_THRESHOLD=0.75
MIN_TRANSITION_SECONDS=5.0
MAX_TRANSITION_SECONDS=180.0

# Offline Sync Configuration
SYNC_ENABLED=true
SYNC_BATCH_SIZE=50
SYNC_RETRY_LIMIT=5

# On-Device / Federated Learning
LEARNING_ENABLED=true
LOCAL_TRAINING_DEVICE=cpu
LOCAL_TRAINING_MAX_EPOCHS=5
MIN_VALIDATED_SAMPLES_FOR_TRAINING=10
FEDERATED_MIN_PARTICIPANTS=2
```

---

## 3. Production Edge Startup

### Step 1: Initialize Database & Base Model
```bash
python -c "from backend.database.connection import init_db; init_db()"
```

### Step 2: Launch System in Production Mode
```bash
# Backend Daemon
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1

# Frontend Production Build (Serve via Nginx or Node static server)
cd frontend
npm run build
```

---

## 4. Backup & Disaster Recovery

### Database & Evidence Backup
To back up the local SQLite state, evidence packages, and model registry:
```bash
# 1. Backup SQLite Database
cp ibvap.db /backup/ibvap_$(date +%Y%m%d_%H%M%S).db

# 2. Backup Evidence Storage
cp -r storage/ /backup/storage_$(date +%Y%m%d_%H%M%S)/

# 3. Backup Model Registry
cp -r models/ /backup/models_$(date +%Y%m%d_%H%M%S)/
```

### Recovery Procedure
To restore from a backup:
1. Stop backend service.
2. Replace `ibvap.db`, `storage/`, and `models/` with backup copies.
3. Restart backend service.
4. Verify `/api/system/health` reports all subsystems healthy.
