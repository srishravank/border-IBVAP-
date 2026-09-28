import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.config import settings
from backend.database.models import Base, CameraModel, ZoneModel, SecurityEventModel

logger = logging.getLogger("ibvap.database")

# Ensure connect_args for SQLite multi-thread safety
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def db_session_scope():
    """Context manager for thread-safe database sessions with automatic commit and rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    """FastAPI Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes database schema and seeds default simulated cameras and virtual fence zones."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")
    
    db: Session = SessionLocal()
    try:
        # 1. Seed Cameras
        count = db.query(CameraModel).count()
        if count < 6:
            logger.info("Seeding/Ensuring initial CCTV cameras (CAM-01 to CAM-06)...")
            initial_cameras = [
                CameraModel(
                    camera_id="CAM-01",
                    camera_name="Sector A - Main Border Gate",
                    location="Sector A (Main Checkpost)",
                    source_type="file",
                    source="data/videos/camera01.mp4",
                    enabled=True,
                    status="OFFLINE",
                    frame_width=1280,
                    frame_height=720,
                    target_fps=25.0,
                    description="Primary vehicular entry gate surveillance camera."
                ),
                CameraModel(
                    camera_id="CAM-02",
                    camera_name="Sector B - Perimeter Fence Alpha",
                    location="Sector B (Northern Perimeter)",
                    source_type="file",
                    source="data/videos/camera02.mp4",
                    enabled=True,
                    status="OFFLINE",
                    frame_width=1280,
                    frame_height=720,
                    target_fps=25.0,
                    description="Perimeter optical sensor overlooking northern wire barrier."
                ),
                CameraModel(
                    camera_id="CAM-03",
                    camera_name="Sector C - Riverine Border Crossing",
                    location="Sector C (River Valley)",
                    source_type="file",
                    source="data/videos/camera03.mp4",
                    enabled=True,
                    status="OFFLINE",
                    frame_width=1280,
                    frame_height=720,
                    target_fps=25.0,
                    description="Low-light optical sensor for riverine infiltration point."
                ),
                CameraModel(
                    camera_id="CAM-04",
                    camera_name="Sector D - Outpost Watchtower Cam",
                    location="Sector D (Observation Tower 4)",
                    source_type="file",
                    source="data/videos/camera04.mp4",
                    enabled=True,
                    status="OFFLINE",
                    frame_width=1280,
                    frame_height=720,
                    target_fps=25.0,
                    description="Long-range border approach monitoring camera."
                ),
                CameraModel(
                    camera_id="CAM-05",
                    camera_name="Sector E - Secondary Vehicle Checkpoint",
                    location="Sector E (Western Flank Checkpost)",
                    source_type="file",
                    source="data/videos/camera01.mp4",
                    enabled=True,
                    status="OFFLINE",
                    frame_width=1280,
                    frame_height=720,
                    target_fps=25.0,
                    description="Western checkpoint secondary inspection camera."
                ),
                CameraModel(
                    camera_id="CAM-06",
                    camera_name="Sector F - Mountain Ridge Optical",
                    location="Sector F (Northern Ridgeline)",
                    source_type="file",
                    source="data/videos/camera02.mp4",
                    enabled=True,
                    status="OFFLINE",
                    frame_width=1280,
                    frame_height=720,
                    target_fps=25.0,
                    description="High altitude optical sensor overlooking ridgeline trail."
                )
            ]
            for cam in initial_cameras:
                existing = db.query(CameraModel).filter(CameraModel.camera_id == cam.camera_id).first()
                if not existing:
                    db.add(cam)
            db.commit()
            logger.info("Default 6 border cameras verified/seeded.")

        # 2. Seed Default Virtual Fence Zones for Border Surveillance
        zone_count = db.query(ZoneModel).count()
        if zone_count < 6:
            logger.info("Seeding initial virtual fence zones...")
            initial_zones = [
                ZoneModel(
                    zone_id="ZONE-CAM01-01",
                    camera_id="CAM-01",
                    zone_name="Sector A - Restricted Gate Corridor",
                    zone_type="restricted",
                    polygon_json='[[400, 200], [880, 200], [920, 700], [360, 700]]',
                    enabled=True,
                    sensitivity="high",
                    description="High security vehicle & personnel gate crossing polygon.",
                    color="#F43F5E"
                ),
                ZoneModel(
                    zone_id="ZONE-CAM02-01",
                    camera_id="CAM-02",
                    zone_name="Sector B - Wire Fence Exclusion Zone",
                    zone_type="restricted",
                    polygon_json='[[50, 300], [1230, 300], [1230, 600], [50, 600]]',
                    enabled=True,
                    sensitivity="high",
                    description="Perimeter exclusion strip along the barbed wire fence.",
                    color="#F43F5E"
                ),
                ZoneModel(
                    zone_id="ZONE-CAM03-01",
                    camera_id="CAM-03",
                    zone_name="Sector C - River Channel Infiltration Zone",
                    zone_type="restricted",
                    polygon_json='[[200, 350], [1100, 350], [1150, 650], [150, 650]]',
                    enabled=True,
                    sensitivity="high",
                    description="River crossing water perimeter monitoring polygon.",
                    color="#F59E0B"
                ),
                ZoneModel(
                    zone_id="ZONE-CAM04-01",
                    camera_id="CAM-04",
                    zone_name="Sector D - Outpost Approach Perimeter",
                    zone_type="restricted",
                    polygon_json='[[300, 200], [980, 200], [1050, 680], [230, 680]]',
                    enabled=True,
                    sensitivity="medium",
                    description="Approach boundary within 200 meters of the watchtower.",
                    color="#06B6D4"
                ),
                ZoneModel(
                    zone_id="ZONE-CAM05-01",
                    camera_id="CAM-05",
                    zone_name="Sector E - Western Approach Gate",
                    zone_type="checkpoint",
                    polygon_json='[[350, 220], [890, 220], [920, 690], [330, 690]]',
                    enabled=True,
                    sensitivity="high",
                    description="Western checkpoint vehicle entry lane boundary.",
                    color="#10B981"
                ),
                ZoneModel(
                    zone_id="ZONE-CAM06-01",
                    camera_id="CAM-06",
                    zone_name="Sector F - Mountain Ridge Trail Zone",
                    zone_type="restricted",
                    polygon_json='[[100, 250], [1180, 250], [1180, 620], [100, 620]]',
                    enabled=True,
                    sensitivity="high",
                    description="High altitude mountain ridge passage exclusion zone.",
                    color="#A855F7"
                )
            ]
            for z in initial_zones:
                existing = db.query(ZoneModel).filter(ZoneModel.zone_id == z.zone_id).first()
                if not existing:
                    db.add(z)
            db.commit()
            logger.info("Default 6 virtual fence zones verified/seeded.")

        # 3. Seed Default Camera Topology Routes
        from backend.database.models import CameraTopologyModel
        topo_count = db.query(CameraTopologyModel).count()
        if topo_count == 0:
            logger.info("Seeding initial camera topology relationships...")
            initial_topology = [
                CameraTopologyModel(
                    relation_id="TOPO-CAM01-CAM02",
                    source_camera="CAM-01",
                    destination_camera="CAM-02",
                    min_transition_seconds=5.0,
                    max_transition_seconds=120.0,
                    distance_meters=45.0,
                    direction="bidirectional",
                    enabled=True,
                    description="Route from Sector A Main Gate along Northern Wire to Sector B."
                ),
                CameraTopologyModel(
                    relation_id="TOPO-CAM02-CAM03",
                    source_camera="CAM-02",
                    destination_camera="CAM-03",
                    min_transition_seconds=8.0,
                    max_transition_seconds=150.0,
                    distance_meters=70.0,
                    direction="bidirectional",
                    enabled=True,
                    description="Route from Sector B Wire Fence descending to Sector C Riverine Crossing."
                ),
                CameraTopologyModel(
                    relation_id="TOPO-CAM03-CAM04",
                    source_camera="CAM-03",
                    destination_camera="CAM-04",
                    min_transition_seconds=10.0,
                    max_transition_seconds=180.0,
                    distance_meters=90.0,
                    direction="bidirectional",
                    enabled=True,
                    description="Route from Sector C Riverine Valley ascending to Sector D Watchtower."
                )
            ]
            db.add_all(initial_topology)
            db.commit()
            logger.info("Default camera topology routes seeded.")

        # 4. Seed Default Phase 5 Risk Configuration
        from backend.database.models import RiskConfigurationModel
        risk_config_count = db.query(RiskConfigurationModel).count()
        if risk_config_count == 0:
            logger.info("Seeding initial Phase 5 Risk Configuration (v1.0.0)...")
            import json
            from datetime import datetime, timezone
            initial_risk_config = RiskConfigurationModel(
                config_version="v1.0.0",
                weights_json=json.dumps({
                    "zone": settings.RISK_WEIGHT_ZONE,
                    "fence": settings.RISK_WEIGHT_FENCE,
                    "night": settings.RISK_WEIGHT_NIGHT,
                    "trajectory": settings.RISK_WEIGHT_TRAJECTORY,
                    "cross_camera": settings.RISK_WEIGHT_CROSS_CAMERA,
                    "vehicle": settings.RISK_WEIGHT_VEHICLE,
                    "behaviour": settings.RISK_WEIGHT_BEHAVIOUR
                }),
                thresholds_json=json.dumps({
                    "low_max": settings.RISK_LOW_MAX,
                    "medium_max": settings.RISK_MEDIUM_MAX,
                    "high_max": settings.RISK_HIGH_MAX
                }),
                night_start_time=settings.NIGHT_START_TIME,
                night_end_time=settings.NIGHT_END_TIME,
                enabled_factors_json=json.dumps([
                    "ZONE_SENSITIVITY",
                    "FENCE_CROSSING",
                    "NIGHT_MOVEMENT",
                    "TRAJECTORY",
                    "CROSS_CAMERA_JOURNEY",
                    "RELATED_VEHICLE_ACTIVITY"
                ]),
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(initial_risk_config)
            db.commit()
            logger.info("Default Phase 5 Risk Configuration seeded.")

    except Exception as e:
        logger.error(f"Error seeding initial database: {e}")
        db.rollback()
    finally:
        db.close()

