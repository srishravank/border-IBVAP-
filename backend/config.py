from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    DATABASE_URL: str = "sqlite:///./ibvap.db"
    
    # Ingestion Defaults
    DEFAULT_TARGET_FPS: float = 25.0
    DEFAULT_FRAME_WIDTH: int = 1280
    DEFAULT_FRAME_HEIGHT: int = 720
    RECONNECT_INTERVAL_SECONDS: float = 3.0
    MAX_RECONNECT_ATTEMPTS: int = 10
    
    # Health Detection
    FROZEN_FRAME_THRESHOLD_SECONDS: float = 8.0
    FROZEN_DIFF_THRESHOLD: float = 0.05
    BLACK_FRAME_MEAN_THRESHOLD: float = 5.0
    BLACK_FRAME_STD_THRESHOLD: float = 2.0
    
    # RTSP
    RTSP_USERNAME: str = ""
    RTSP_PASSWORD: str = ""
    
    # Phase 2: AI Perception & Tracking
    AI_ENABLED: bool = True
    AI_DETECTOR_TYPE: str = "yolo"  # "yolo", "rtdetr", "mock"
    AI_MODEL_PATH: str = "yolov8n.pt"
    DETECTION_CONFIDENCE: float = 0.35
    IOU_THRESHOLD: float = 0.45
    AI_DEVICE: str = "auto"  # "auto", "cpu", "cuda"
    PROCESS_EVERY_N_FRAMES: int = 1
    TRAJECTORY_HISTORY_LENGTH: int = 30
    TRACK_MAX_AGE: int = 30
    TRACK_MATCH_THRESH: float = 0.8
    LOW_LIGHT_ENHANCEMENT: bool = False
    
    # Phase 3: Event & Verification Engine
    ZONE_ENABLED: bool = True
    VERIFICATION_REQUIRED_FRAMES: int = 3
    VERIFICATION_WINDOW_FRAMES: int = 5
    MIN_TRACK_CONFIDENCE: float = 0.40
    MIN_TRACK_AGE_FRAMES: int = 2
    SPATIAL_MAX_DISPLACEMENT_PX: float = 250.0
    EVENT_RETENTION_HOURS: int = 24
    MAX_CANDIDATE_AGE_FRAMES: int = 15

    # Phase 4: Cross-Camera Intelligence & Incident Graph
    CROSS_CAMERA_MATCH_THRESHOLD: float = 0.75
    MIN_TRANSITION_SECONDS: float = 5.0
    MAX_TRANSITION_SECONDS: float = 180.0
    SUBJECT_HISTORY_MINUTES: int = 30
    APPEARANCE_WEIGHT: float = 0.40
    TEMPORAL_WEIGHT: float = 0.25
    TOPOLOGY_WEIGHT: float = 0.20
    TRAJECTORY_WEIGHT: float = 0.15
    VEHICLE_PROXIMITY_MAX_SECONDS: float = 60.0
    VEHICLE_PROXIMITY_MAX_DISTANCE_PX: float = 300.0
    
    # Phase 5: Intelligence & Explainable Risk Engine
    RISK_WEIGHT_ZONE: float = 20.0
    RISK_WEIGHT_FENCE: float = 25.0
    RISK_WEIGHT_NIGHT: float = 15.0
    RISK_WEIGHT_TRAJECTORY: float = 15.0
    RISK_WEIGHT_CROSS_CAMERA: float = 10.0
    RISK_WEIGHT_VEHICLE: float = 10.0
    RISK_WEIGHT_BEHAVIOUR: float = 5.0
    
    RISK_LOW_MAX: float = 30.0
    RISK_MEDIUM_MAX: float = 65.0
    RISK_HIGH_MAX: float = 100.0
    
    NIGHT_START_TIME: str = "20:00"  # 24-hour format HH:MM
    NIGHT_END_TIME: str = "05:00"
    
    RISK_BEHAVIOUR_ENABLED: bool = False
    RISK_ASSESSMENT_COOLDOWN_SECONDS: float = 2.0

    # Phase 8: Offline-First Operation & Resilient Synchronization
    EDGE_ID: str = "EDGE-SECTOR-A-01"
    CONNECTIVITY_CHECK_INTERVAL: float = 10.0
    SYNC_ENABLED: bool = True
    SYNC_BATCH_SIZE: int = 50
    SYNC_RETRY_LIMIT: int = 5
    SYNC_RETRY_BACKOFF_BASE: float = 5.0
    MAX_LOCAL_STORAGE_MB: int = 5120
    MAX_QUEUE_SIZE: int = 10000

    # Phase 9: On-Device / Federated Learning
    LEARNING_ENABLED: bool = True
    LOCAL_TRAINING_DEVICE: str = "cpu"
    LOCAL_TRAINING_MAX_EPOCHS: int = 5
    LOCAL_TRAINING_BATCH_SIZE: int = 16
    LOCAL_TRAINING_LEARNING_RATE: float = 0.001
    MIN_VALIDATED_SAMPLES_FOR_TRAINING: int = 10
    FEDERATED_MIN_PARTICIPANTS: int = 2
    MODEL_REGISTRY_DIR: str = "models/registry"
    MAX_TRAINING_TIME_SECONDS: float = 120.0
    TRAINING_DATA_RETENTION_DAYS: int = 30
    # Phase 11: Final Validation, Demo & Jury Readiness
    DEMO_MODE: bool = True
    JURY_MODE: bool = False
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

