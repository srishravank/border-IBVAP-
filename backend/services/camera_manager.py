import time
import threading
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timezone

from backend.config import settings
from backend.models.camera import (
    CameraSourceType,
    CameraStatus,
    CameraConfigCreate,
    CameraConfigUpdate,
    CameraResponse,
    CameraStatusResponse
)
from backend.models.frame import FrameMetadata, FramePacket
from backend.models.event import CameraEvent, EventType
from backend.health.camera_health import CameraHealthMonitor
from backend.services.video_source import BaseVideoSource
from backend.services.file_source import FileSource
from backend.services.webcam_source import WebcamSource
from backend.services.rtsp_source import RTSPSource
from backend.database.connection import SessionLocal
from backend.database.models import CameraModel, CameraHealthEventModel

logger = logging.getLogger("ibvap.manager")


class CameraWorker:
    """
    Dedicated ingestion worker for a single CCTV camera stream.
    Runs an independent capture loop in a separate thread for fault isolation.
    """

    def __init__(
        self,
        camera_model: CameraModel,
        on_event: Optional[Callable[[CameraEvent], None]] = None,
        on_frame_hook: Optional[Callable[[FramePacket], None]] = None
    ):
        self.camera_id = camera_model.camera_id
        self.camera_name = camera_model.camera_name
        self.location = camera_model.location
        self.source_type = CameraSourceType(camera_model.source_type)
        self.source_uri = camera_model.source
        self.target_fps = camera_model.target_fps or settings.DEFAULT_TARGET_FPS
        self.configured_width = camera_model.frame_width or settings.DEFAULT_FRAME_WIDTH
        self.configured_height = camera_model.frame_height or settings.DEFAULT_FRAME_HEIGHT
        self.enabled = camera_model.enabled
        self.description = camera_model.description or ""
        self.extra_config = camera_model.extra_config

        self.on_event = on_event
        self.on_frame_hook = on_frame_hook

        self.source: Optional[BaseVideoSource] = None
        self.health_monitor = CameraHealthMonitor(
            camera_id=self.camera_id,
            on_event_callback=self._handle_health_event
        )

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False

        self.latest_frame_packet: Optional[FramePacket] = None
        self.frame_counter: int = 0
        self.lock = threading.Lock()

        self._init_source()

    def _init_source(self):
        """Instantiates the appropriate video source implementation."""
        if self.source_type == CameraSourceType.FILE:
            self.source = FileSource(
                camera_id=self.camera_id,
                file_path=self.source_uri,
                loop=True,
                target_fps=self.target_fps
            )
        elif self.source_type == CameraSourceType.WEBCAM:
            self.source = WebcamSource(
                camera_id=self.camera_id,
                device_index=self.source_uri,
                target_fps=self.target_fps
            )
        elif self.source_type == CameraSourceType.RTSP:
            self.source = RTSPSource(
                camera_id=self.camera_id,
                rtsp_url=self.source_uri,
                target_fps=self.target_fps,
                extra_config=self.extra_config
            )
        else:
            raise ValueError(f"Unsupported source type: {self.source_type}")

    def _handle_health_event(self, event: CameraEvent):
        """Passes health event up to the manager and listeners."""
        if self.on_event:
            self.on_event(event)

    def start(self):
        """Starts the dedicated ingestion thread."""
        if self._is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._ingestion_loop,
            name=f"CameraWorker-{self.camera_id}",
            daemon=True
        )
        self._is_running = True
        self._thread.start()
        logger.info(f"[{self.camera_id}] Ingestion worker started")

    def stop(self):
        """Signals the ingestion thread to stop and releases resources."""
        if not self._is_running:
            return
        self._stop_event.set()
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        
        if self.source:
            self.source.release()
        
        self.health_monitor.record_disconnect("Worker stopped manually")
        logger.info(f"[{self.camera_id}] Ingestion worker stopped")

    def _ingestion_loop(self):
        """Independent ingestion loop with automatic fault detection and reconnect logic."""
        reconnect_interval = settings.RECONNECT_INTERVAL_SECONDS
        max_reconnects = settings.MAX_RECONNECT_ATTEMPTS

        while not self._stop_event.is_set():
            # 1. Connect if not connected
            if not self.source.is_connected():
                self.health_monitor.record_reconnecting("Establishing source connection")
                connected = False
                try:
                    connected = self.source.connect()
                except Exception as e:
                    logger.error(f"[{self.camera_id}] Connection exception: {e}")

                if not connected:
                    self.health_monitor.record_disconnect("Failed to connect to video source")
                    # Backoff before retrying
                    for _ in range(int(reconnect_interval * 10)):
                        if self._stop_event.is_set():
                            break
                        time.sleep(0.1)
                    continue
                else:
                    self.health_monitor.reset_reconnect_counter()

            # 2. Read frame
            try:
                ret, frame = self.source.read_frame()
            except Exception as e:
                logger.error(f"[{self.camera_id}] Read frame exception: {e}")
                ret, frame = False, None

            if not ret or frame is None:
                self.health_monitor.record_disconnect("Stream read failed or stream closed")
                self.source.release()
                time.sleep(reconnect_interval)
                continue

            # 3. Standardize resolution to configured width/height if needed
            h, w = frame.shape[:2]
            if self.configured_width and self.configured_height:
                if w != self.configured_width or h != self.configured_height:
                    import cv2
                    frame = cv2.resize(frame, (self.configured_width, self.configured_height), interpolation=cv2.INTER_AREA)
                    h, w = self.configured_height, self.configured_width

            self.frame_counter += 1
            metadata = FrameMetadata(
                camera_id=self.camera_id,
                frame_id=self.frame_counter,
                timestamp=datetime.now(timezone.utc).isoformat(),
                width=w,
                height=h,
                fps=self.health_monitor.current_fps or self.target_fps,
                source_type=self.source_type.value
            )

            packet = FramePacket(metadata=metadata, frame=frame)
            with self.lock:
                self.latest_frame_packet = packet

            # 4. Perform health inspection (frozen frame / black frame / fps)
            self.health_monitor.process_frame(frame, self.frame_counter)

            # 5. Zero-copy handoff hook for Phase 2 AI (YOLO/RT-DETR/ByteTrack)
            if self.on_frame_hook:
                try:
                    self.on_frame_hook(packet)
                except Exception as e:
                    logger.error(f"[{self.camera_id}] Frame hook exception: {e}")

        # Cleanup on exit
        if self.source:
            self.source.release()

    def get_latest_frame(self) -> Optional[FramePacket]:
        with self.lock:
            return self.latest_frame_packet

    def get_status_response(self) -> CameraStatusResponse:
        res_str = f"{self.configured_width}x{self.configured_height}"
        last_ts = None
        if self.latest_frame_packet:
            res_str = f"{self.latest_frame_packet.metadata.width}x{self.latest_frame_packet.metadata.height}"
            last_ts = self.latest_frame_packet.metadata.timestamp

        return CameraStatusResponse(
            camera_id=self.camera_id,
            camera_name=self.camera_name,
            status=self.health_monitor.current_status,
            source_type=self.source_type,
            source=self.source_uri,
            is_ingesting=self._is_running,
            fps=self.health_monitor.current_fps,
            resolution=res_str,
            last_frame_timestamp=last_ts,
            total_frames_ingested=self.frame_counter,
            reconnect_attempts=self.health_monitor.reconnect_attempts,
            health_message=self.health_monitor.last_error_message or "Normal",
            uptime_seconds=self.health_monitor.get_uptime_seconds()
        )


class CameraManager:
    """
    Central Video Ingestion Manager for IBVAP 2.0.
    Orchestrates multiple camera workers, coordinates database synchronization,
    and publishes structured events to subscribers.
    """

    def __init__(self):
        self.workers: Dict[str, CameraWorker] = {}
        self.event_subscribers: List[Callable[[CameraEvent], None]] = []
        self.frame_hooks: List[Callable[[FramePacket], None]] = []
        self._lock = threading.Lock()

    def register_event_subscriber(self, callback: Callable[[CameraEvent], None]):
        """Subscribes to all real-time camera health and status events (used by WebSockets)."""
        if callback not in self.event_subscribers:
            self.event_subscribers.append(callback)

    def unregister_event_subscriber(self, callback: Callable[[CameraEvent], None]):
        if callback in self.event_subscribers:
            self.event_subscribers.remove(callback)

    def register_frame_hook(self, hook: Callable[[FramePacket], None]):
        """
        Registers an AI pipeline frame consumer (e.g., Phase 2 YOLO / ByteTrack).
        Receives every valid captured frame without copying.
        """
        if hook not in self.frame_hooks:
            self.frame_hooks.append(hook)

    def _broadcast_event(self, event: CameraEvent):
        """Broadcasts event to subscribers and logs to the database."""
        # 1. Dispatch in-memory
        for sub in list(self.event_subscribers):
            try:
                sub(event)
            except Exception as e:
                logger.error(f"Event subscriber error: {e}")

        # 2. Persist to DB asynchronously/safely
        try:
            db = SessionLocal()
            try:
                # Update camera status in DB
                cam = db.query(CameraModel).filter(CameraModel.camera_id == event.camera_id).first()
                if cam and event.event_type in (
                    EventType.CAMERA_ONLINE,
                    EventType.CAMERA_OFFLINE,
                    EventType.CAMERA_RECONNECTING,
                    EventType.FRAME_FROZEN,
                    EventType.INVALID_FRAME
                ):
                    status_map = {
                        EventType.CAMERA_ONLINE: "ONLINE",
                        EventType.CAMERA_OFFLINE: "OFFLINE",
                        EventType.CAMERA_RECONNECTING: "RECONNECTING",
                        EventType.FRAME_FROZEN: "FROZEN",
                        EventType.INVALID_FRAME: "BLACK_FRAME",
                    }
                    cam.status = status_map.get(event.event_type, cam.status)
                    if event.event_type == EventType.CAMERA_ONLINE:
                        cam.last_seen = datetime.now(timezone.utc)
                    db.commit()

                # Log event record
                health_evt = CameraHealthEventModel(
                    camera_id=event.camera_id,
                    event_type=event.event_type.value,
                    frame_id=event.frame_id,
                    description=event.message,
                    details_json=str(event.details)
                )
                db.add(health_evt)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to persist event to DB: {e}")

    def _dispatch_frame(self, packet: FramePacket):
        """Dispatches frame to Phase 2 AI consumers."""
        for hook in list(self.frame_hooks):
            try:
                hook(packet)
            except Exception as e:
                logger.error(f"Frame hook error: {e}")

    def load_cameras_from_db(self):
        """Loads all enabled cameras from database and initializes workers."""
        db = SessionLocal()
        try:
            cameras = db.query(CameraModel).all()
            for cam in cameras:
                self.add_camera_worker(cam, start_immediately=cam.enabled)
        finally:
            db.close()

    def add_camera_worker(self, cam_model: CameraModel, start_immediately: bool = True) -> CameraWorker:
        with self._lock:
            if cam_model.camera_id in self.workers:
                # Stop existing worker first
                self.workers[cam_model.camera_id].stop()

            worker = CameraWorker(
                camera_model=cam_model,
                on_event=self._broadcast_event,
                on_frame_hook=self._dispatch_frame
            )
            self.workers[cam_model.camera_id] = worker
            if start_immediately and cam_model.enabled:
                worker.start()
            return worker

    def register_camera(self, config: CameraConfigCreate) -> CameraResponse:
        """Registers a new camera in the database and spins up its ingestion worker."""
        db = SessionLocal()
        try:
            existing = db.query(CameraModel).filter(CameraModel.camera_id == config.camera_id).first()
            if existing:
                raise ValueError(f"Camera with ID '{config.camera_id}' already exists")

            cam_model = CameraModel(
                camera_id=config.camera_id,
                camera_name=config.camera_name,
                location=config.location,
                source_type=config.source_type.value,
                source=config.source,
                enabled=config.enabled,
                target_fps=config.target_fps or settings.DEFAULT_TARGET_FPS,
                frame_width=config.frame_width or settings.DEFAULT_FRAME_WIDTH,
                frame_height=config.frame_height or settings.DEFAULT_FRAME_HEIGHT,
                description=config.description,
                extra_config=config.extra_config or {}
            )
            db.add(cam_model)
            db.commit()
            db.refresh(cam_model)

            worker = self.add_camera_worker(cam_model, start_immediately=config.enabled)
            return self.get_camera_response(config.camera_id)
        finally:
            db.close()

    def update_camera(self, camera_id: str, update: CameraConfigUpdate) -> CameraResponse:
        """Updates camera configuration and restarts worker if necessary."""
        db = SessionLocal()
        try:
            cam_model = db.query(CameraModel).filter(CameraModel.camera_id == camera_id).first()
            if not cam_model:
                raise KeyError(f"Camera '{camera_id}' not found")

            if update.camera_name is not None:
                cam_model.camera_name = update.camera_name
            if update.location is not None:
                cam_model.location = update.location
            if update.source_type is not None:
                cam_model.source_type = update.source_type.value
            if update.source is not None:
                cam_model.source = update.source
            if update.enabled is not None:
                cam_model.enabled = update.enabled
            if update.description is not None:
                cam_model.description = update.description
            if update.target_fps is not None:
                cam_model.target_fps = update.target_fps
            if update.frame_width is not None:
                cam_model.frame_width = update.frame_width
            if update.frame_height is not None:
                cam_model.frame_height = update.frame_height
            if update.extra_config is not None:
                cam_model.extra_config = update.extra_config

            db.commit()
            db.refresh(cam_model)

            # Refresh runtime worker
            self.add_camera_worker(cam_model, start_immediately=cam_model.enabled)
            return self.get_camera_response(camera_id)
        finally:
            db.close()

    def delete_camera(self, camera_id: str) -> bool:
        """Stops worker and deletes camera from database."""
        with self._lock:
            if camera_id in self.workers:
                self.workers[camera_id].stop()
                del self.workers[camera_id]

        try:
            from backend.services.ai_pipeline import ai_service
            ai_service.remove_camera_pipeline(camera_id)
        except Exception:
            pass

        db = SessionLocal()
        try:
            cam_model = db.query(CameraModel).filter(CameraModel.camera_id == camera_id).first()
            if cam_model:
                db.delete(cam_model)
                db.commit()
                return True
            return False
        finally:
            db.close()

    def start_camera(self, camera_id: str) -> bool:
        worker = self.workers.get(camera_id)
        if worker:
            worker.start()
            return True
        return False

    def stop_camera(self, camera_id: str) -> bool:
        worker = self.workers.get(camera_id)
        if worker:
            worker.stop()
            return True
        return False

    def get_camera_response(self, camera_id: str) -> CameraResponse:
        db = SessionLocal()
        try:
            cam_model = db.query(CameraModel).filter(CameraModel.camera_id == camera_id).first()
            if not cam_model:
                raise KeyError(f"Camera '{camera_id}' not found")

            worker = self.workers.get(camera_id)
            status = worker.health_monitor.current_status if worker else CameraStatus.OFFLINE
            fps = worker.health_monitor.current_fps if worker else 0.0
            total_frames = worker.frame_counter if worker else 0
            reconnect_attempts = worker.health_monitor.reconnect_attempts if worker else 0
            
            actual_w = worker.source.width if (worker and worker.source) else cam_model.frame_width
            actual_h = worker.source.height if (worker and worker.source) else cam_model.frame_height

            return CameraResponse(
                camera_id=cam_model.camera_id,
                camera_name=cam_model.camera_name,
                location=cam_model.location,
                source_type=CameraSourceType(cam_model.source_type),
                source=cam_model.source,
                enabled=cam_model.enabled,
                status=status,
                description=cam_model.description,
                target_fps=cam_model.target_fps,
                frame_width=cam_model.frame_width,
                frame_height=cam_model.frame_height,
                fps=fps,
                actual_width=actual_w,
                actual_height=actual_h,
                total_frames_ingested=total_frames,
                reconnect_attempts=reconnect_attempts,
                created_at=cam_model.created_at.isoformat() if cam_model.created_at else "",
                last_seen=cam_model.last_seen.isoformat() if cam_model.last_seen else None,
                extra_config=cam_model.extra_config
            )
        finally:
            db.close()

    def get_all_cameras(self) -> List[CameraResponse]:
        db = SessionLocal()
        try:
            cams = db.query(CameraModel).all()
            return [self.get_camera_response(c.camera_id) for c in cams]
        finally:
            db.close()

    def get_camera_status(self, camera_id: str) -> CameraStatusResponse:
        worker = self.workers.get(camera_id)
        if not worker:
            raise KeyError(f"Camera '{camera_id}' not found in active manager")
        return worker.get_status_response()

    def get_latest_frame_jpeg(self, camera_id: str) -> Optional[bytes]:
        worker = self.workers.get(camera_id)
        if worker:
            frame_pkt = worker.get_latest_frame()
            if frame_pkt:
                return frame_pkt.to_jpeg()
        return None

    def shutdown_all(self):
        """Stops all running camera workers gracefully."""
        logger.info("Shutting down all camera ingestion workers...")
        with self._lock:
            for worker in self.workers.values():
                worker.stop()
            self.workers.clear()


# Global singleton camera manager instance
camera_manager = CameraManager()
