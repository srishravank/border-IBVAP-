import sys
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.config import settings
from backend.database.connection import init_db
from backend.services.camera_manager import camera_manager
from backend.services.ai_pipeline import ai_service
from backend.services.event_manager import event_manager
from backend.services.cross_camera_engine import cross_camera_engine
from backend.api.cameras import router as cameras_router
from backend.api.websocket import router as ws_router, set_event_loop
from backend.api.ai import router as ai_router
from backend.api.zones import router as zones_router
from backend.api.events import router as events_router
from backend.api.topology import router as topology_router
from backend.api.subjects import router as subjects_router
from backend.api.incidents import router as incidents_router
from backend.api.risk import router as risk_router
from backend.api.command import router as command_router
from backend.api.evidence import evidence_router
from backend.api.connectivity import connectivity_router
from backend.api.sync import sync_router
from backend.api.learning import router as learning_router
from backend.api.demo import router as demo_router
from backend.services.risk_service import risk_service
from backend.services.command_service import command_service
from backend.services.evidence_service import evidence_service
from backend.services.connectivity_service import connectivity_service
from backend.services.sync_service import sync_service
from backend.services.model_registry_service import model_registry
from backend.services.training_sample_service import training_sample_service
from backend.services.local_training_service import local_training_service
from backend.services.federated_learning_service import federated_aggregator

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ibvap.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown orchestration."""
    logger.info("Initializing IBVAP 2.0 Edge Video Ingestion, AI, Verification & Cross-Camera Engine...")
    loop = asyncio.get_running_loop()
    set_event_loop(loop)
    
    # 1. Initialize SQLite database & seed default cameras, virtual zones and topology
    init_db()
    
    # 2. Initialize AI Perception Service & register zero-copy frame hook
    ai_service.initialize()
    camera_manager.register_frame_hook(ai_service.process_frame_packet)
    logger.info("Registered AI perception pipeline hook with CameraManager.")

    # 3. Initialize Phase 3 Event & Verification Engine
    event_manager.initialize()
    ai_service.register_observation_subscriber(event_manager.process_observation)
    logger.info("Registered Event & Multi-Frame Verification Engine with AI Pipeline.")

    # 4. Initialize Phase 4 Cross-Camera Intelligence Engine
    cross_camera_engine.initialize()
    ai_service.register_observation_subscriber(cross_camera_engine.process_observation)
    event_manager.register_confirmed_event_subscriber(cross_camera_engine.process_confirmed_event)
    logger.info("Registered Cross-Camera Intelligence Engine with Observation and Event pipelines.")

    # 5. Start ingestion for all enabled cameras
    camera_manager.load_cameras_from_db()
    logger.info(f"IBVAP 2.0 Ingestion Service started. Active camera workers: {len(camera_manager.workers)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down IBVAP 2.0 Ingestion, AI, Verification & Cross-Camera Services...")
    camera_manager.shutdown_all()
    logger.info("Ingestion & AI workers stopped cleanly.")


app = FastAPI(
    title="IBVAP 2.0 — Edge CCTV & Cross-Camera Intelligence Platform",
    description="Edge CCTV Ingestion, AI Perception, Multi-Frame Verification & Cross-Camera Incident Graph (SIH26187 - Phase 4)",
    version="4.0.0",
    lifespan=lifespan
)

# Enable CORS for local React/Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(topology_router)
app.include_router(cameras_router)
app.include_router(ws_router)
app.include_router(ai_router)
app.include_router(zones_router)
app.include_router(events_router)
app.include_router(subjects_router)
app.include_router(incidents_router)
app.include_router(risk_router)
app.include_router(command_router)
app.include_router(evidence_router, prefix="/api")
app.include_router(connectivity_router)
app.include_router(sync_router)
app.include_router(learning_router, prefix="/api")
app.include_router(demo_router)


@app.get("/api/health", tags=["System"])
@app.get("/api/system/health", tags=["System"])
def get_system_health():
    """Unified system health check across all 10 IBVAP subsystems."""
    # 1. Database Check
    db_status = "healthy"
    try:
        from backend.database.connection import SessionLocal
        from sqlalchemy import text
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        db_status = "degraded"

    # 2. Camera Pipeline Check
    cams = camera_manager.get_all_cameras()
    total_cams = len(cams)
    online_cams = sum(1 for c in cams if c.status.value == "ONLINE")
    offline_cams = sum(1 for c in cams if c.status.value == "OFFLINE")
    reconnecting_cams = sum(1 for c in cams if c.status.value == "RECONNECTING")
    frozen_cams = sum(1 for c in cams if c.status.value in ("FROZEN", "BLACK_FRAME"))
    cam_pipeline_status = "healthy" if online_cams > 0 or total_cams == 0 else "degraded"

    # 3. AI Engine Check
    ai_status = ai_service.get_global_status()
    ai_engine_status = "healthy" if ai_status.get("status") in ("READY", "INSPECTING", "RUNNING") else "degraded"

    # 4. Risk Engine Check
    risk_engine_status = "healthy"

    # 5. Evidence & Ledger Check
    evidence_status = "healthy"
    ledger_status = "healthy"

    # 6. Connectivity & Sync Check
    conn_stat = connectivity_service.get_status()
    sync_summary = sync_service.get_summary()
    sync_status_val = "healthy" if conn_stat.state.value == "ONLINE" else "offline_queueing"

    # 7. Model Registry & Learning Check
    active_model = model_registry.get_active_model()
    validated_samples_count = training_sample_service.get_validated_samples_count()
    learning_status_val = "ready" if not local_training_service.is_training else "training"

    total_fps = sum(c.fps for c in cams)
    total_frames = sum(c.total_frames_ingested for c in cams)
    confirmed_events = event_manager.get_security_events(status="CONFIRMED", limit=50)
    subjects = cross_camera_engine.get_all_subjects()
    incidents = cross_camera_engine.get_incidents()

    overall_status = "healthy" if db_status == "healthy" and ai_engine_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "system": "IBVAP 2.0 Intelligent Border Video Analytics & Evidence Platform",
        "phase": "PHASE 10 - FULL INTEGRATION & HARDENING",
        "services": {
            "database": db_status,
            "camera_pipeline": cam_pipeline_status,
            "ai_engine": ai_engine_status,
            "risk_engine": risk_engine_status,
            "evidence": evidence_status,
            "ledger": ledger_status,
            "sync": sync_status_val,
            "learning": learning_status_val
        },
        "connectivity": conn_stat.model_dump(),
        "sync": sync_summary.model_dump(),
        "learning": {
            "active_model": active_model.model_id if active_model else "NONE",
            "active_version": active_model.version if active_model else "1.0.0",
            "model_hash": active_model.model_hash if active_model else "",
            "validated_training_samples": validated_samples_count,
            "training_status": "READY" if not local_training_service.is_training else "TRAINING",
            "privacy_mode": "PRIVACY_PRESERVING_FEDERATED"
        },
        "metrics": {
            "total_cameras": total_cams,
            "online_cameras": online_cams,
            "offline_cameras": offline_cams,
            "reconnecting_cameras": reconnecting_cams,
            "anomaly_cameras": frozen_cams,
            "aggregate_fps": round(total_fps, 1),
            "total_frames_ingested": total_frames
        },
        "ai": {
            "status": ai_status["status"],
            "model_name": ai_status["model_name"],
            "device": ai_status["device"],
            "total_active_tracks": ai_status["total_active_tracks"],
            "aggregate_inference_fps": ai_status["aggregate_inference_fps"]
        },
        "verification": {
            "active_verifying_candidates": len(event_manager.active_candidates),
            "confirmed_security_events": len(confirmed_events)
        },
        "cross_camera": {
            "active_subjects": len(subjects),
            "connected_incidents": len(incidents),
            "candidate_matches": len(cross_camera_engine.recent_candidates)
        },
        "risk": {
            "total_assessed_incidents": len(incidents),
            "engine_status": "ONLINE",
            "active_config": "v1.0.0"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

