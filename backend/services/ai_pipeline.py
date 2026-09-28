import time
import logging
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable
import numpy as np

from backend.config import settings
from backend.models.frame import FramePacket
from backend.models.detection import DetectionResult, DetectionSummary
from backend.models.track import TrackedObject, TrackState as TrackLifecycleState
from backend.models.event import CameraEvent, EventType
from ai.schemas.observation import AIObservation, ObservedObjectSummary
from ai.detection.base_detector import BaseObjectDetector
from ai.detection.yolo_detector import YOLODetector
from ai.detection.rtdetr_detector import RTDETRDetector
from ai.detection.mock_detector import MockDetector
from ai.tracking.bytetrack_tracker import ByteTrackTracker
from ai.preprocessing.frame_preprocessor import IdentityPreprocessor, LowLightPreprocessor, BaseFramePreprocessor
from backend.services.ai_annotator import annotate_frame

logger = logging.getLogger("ibvap.ai.pipeline")


import queue


class CameraAIPipeline:
    """
    Per-camera AI Perception pipeline.
    Executes frame preprocessing, object detection, ByteTrack tracking,
    and formats standardized observations.
    """

    def __init__(
        self,
        camera_id: str,
        detector: BaseObjectDetector,
        preprocessor: Optional[BaseFramePreprocessor] = None,
        on_event_callback: Optional[Callable[[CameraEvent], None]] = None,
        on_observation_callback: Optional[Callable[[AIObservation], None]] = None
    ):
        self.camera_id = camera_id
        self.detector = detector
        self.preprocessor = preprocessor or (LowLightPreprocessor() if settings.LOW_LIGHT_ENHANCEMENT else IdentityPreprocessor())
        self.on_event_callback = on_event_callback
        self.on_observation_callback = on_observation_callback

        self.tracker = ByteTrackTracker(
            camera_id=camera_id,
            track_thresh=settings.DETECTION_CONFIDENCE,
            match_thresh=settings.TRACK_MATCH_THRESH,
            track_buffer=settings.TRACK_MAX_AGE,
            frame_rate=int(settings.DEFAULT_TARGET_FPS),
            trajectory_history_length=settings.TRAJECTORY_HISTORY_LENGTH
        )

        self.lock = threading.Lock()
        self.status = "INITIALIZING"
        self.last_error = ""

        # Latest states
        self.latest_detections: List[DetectionResult] = []
        self.active_tracks: List[TrackedObject] = []
        self.recent_observations: List[AIObservation] = []
        self.annotated_jpeg: Optional[bytes] = None
        self._previous_track_ids: set = set()

        # Performance metrics
        self.processed_frames = 0
        self.skipped_frames = 0
        self.last_inference_time_ms = 0.0
        self.last_detector_time_ms = 0.0
        self.last_tracker_time_ms = 0.0
        self.last_total_pipeline_ms = 0.0
        self._fps_timestamps: List[float] = []
        self.inference_fps = 0.0
        self.obs_counter = 0

        # Asynchronous non-blocking worker queue (drops frames if worker is busy)
        self._frame_queue: queue.Queue = queue.Queue(maxsize=1)
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(
            target=self._ai_worker_loop,
            name=f"AIWorker-{self.camera_id}",
            daemon=True
        )
        self._worker_thread.start()

    def enqueue_frame(self, packet: FramePacket):
        """Non-blocking frame enqueue: replaces pending frame if AI worker is busy."""
        try:
            try:
                self._frame_queue.get_nowait()
            except queue.Empty:
                pass
            self._frame_queue.put_nowait(packet)
        except Exception:
            pass

    def _ai_worker_loop(self):
        """Background thread executing neural inference without blocking video ingestion."""
        while not self._stop_event.is_set():
            try:
                packet = self._frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                self.process_frame(packet)
            except Exception as e:
                logger.error(f"[{self.camera_id}] Async AI worker loop error: {e}")

    def stop(self):
        """Signals AI worker thread to terminate."""
        self._stop_event.set()

    def process_frame(self, packet: FramePacket):
        """Processes a single incoming video frame through the AI perception pipeline."""
        now = time.time()
        self.processed_frames += 1

        # Frame skipping logic
        if settings.PROCESS_EVERY_N_FRAMES > 1 and (self.processed_frames % settings.PROCESS_EVERY_N_FRAMES != 0):
            self.skipped_frames += 1
            return

        # Track rolling inference FPS
        self._fps_timestamps.append(now)
        self._fps_timestamps = [t for t in self._fps_timestamps if now - t <= 1.0]
        self.inference_fps = round(len(self._fps_timestamps), 1)

        t_start = time.perf_counter()

        try:
            raw_frame = packet.frame
            if raw_frame is None or raw_frame.size == 0:
                return

            # 1. Preprocessing (e.g. low-light CLAHE if enabled)
            preprocessed_frame = self.preprocessor.preprocess(raw_frame)

            # 2. Object Detection
            t_det_start = time.perf_counter()
            detections = self.detector.detect(preprocessed_frame)
            t_det_end = time.perf_counter()
            self.last_detector_time_ms = round((t_det_end - t_det_start) * 1000.0, 2)

            # Attach camera ID and frame ID to detections
            for d in detections:
                d.camera_id = self.camera_id
                d.frame_id = packet.metadata.frame_id
                d.timestamp = packet.metadata.timestamp

            # 3. Multi-Object Tracking with ByteTrack
            t_track_start = time.perf_counter()
            tracks = self.tracker.update(detections, frame_id=packet.metadata.frame_id)
            t_track_end = time.perf_counter()
            self.last_tracker_time_ms = round((t_track_end - t_track_start) * 1000.0, 2)

            t_total_end = time.perf_counter()
            self.last_inference_time_ms = self.last_detector_time_ms
            self.last_total_pipeline_ms = round((t_total_end - t_start) * 1000.0, 2)
            self.status = "RUNNING"
            self.last_error = ""

            # 4. Generate Standardized AI Observations for Phase 3
            current_track_ids = set()
            new_observations: List[AIObservation] = []

            for track in tracks:
                current_track_ids.add(track.track_id)
                self.obs_counter += 1
                obs_id = f"OBS-{self.camera_id}-{self.obs_counter:06d}"

                summary_obj = ObservedObjectSummary(
                    track_id=track.track_id,
                    formatted_id=track.formatted_id,
                    type=track.object_type,
                    class_name=track.class_name,
                    subclass=track.subclass,
                    confidence=track.confidence,
                    bbox=track.bbox,
                    center=track.center
                )

                obs = AIObservation(
                    observation_id=obs_id,
                    camera_id=self.camera_id,
                    frame_id=packet.metadata.frame_id,
                    timestamp=packet.metadata.timestamp,
                    object=summary_obj,
                    trajectory=list(track.trajectory),
                    metadata={
                        "fps": self.inference_fps,
                        "inference_ms": self.last_total_pipeline_ms,
                        "detector": self.detector.model_name
                    }
                )
                new_observations.append(obs)

                if self.on_observation_callback:
                    try:
                        self.on_observation_callback(obs)
                    except Exception as e:
                        logger.error(f"[{self.camera_id}] Observation callback error: {e}")

            # 5. Emit AI Tracking Events
            self._handle_track_lifecycle_events(current_track_ids, tracks, packet.metadata.frame_id, packet.metadata.timestamp)

            # 6. Annotate Visual Frame (with virtual fence polygons and verification candidates)
            from backend.services.zone_engine import zone_engine
            from backend.services.event_manager import event_manager

            active_zones = zone_engine.get_zones_for_camera(self.camera_id, enabled_only=True)
            active_cands = event_manager.get_active_verifying_candidates(self.camera_id)

            annotated_bgr = annotate_frame(
                frame=raw_frame,
                tracks=tracks,
                detections=detections,
                zones=active_zones,
                active_candidates=active_cands,
                fps=self.inference_fps,
                inference_ms=self.last_total_pipeline_ms,
                model_name=self.detector.model_name
            )

            # 7. Thread-safe snapshot updates
            with self.lock:
                self.latest_detections = detections
                self.active_tracks = tracks
                self.recent_observations = (new_observations + self.recent_observations)[:50]
                self._update_annotated_jpeg(annotated_bgr)

        except Exception as e:
            self.status = "ERROR"
            self.last_error = str(e)
            logger.error(f"[{self.camera_id}] AI pipeline error: {e}", exc_info=True)

    def _update_annotated_jpeg(self, frame_bgr: np.ndarray):
        import cv2
        success, encoded = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        if success:
            self.annotated_jpeg = encoded.tobytes()

    def _handle_track_lifecycle_events(self, current_ids: set, tracks: List[TrackedObject], frame_id: int, timestamp: str):
        """Emits OBJECT_TRACK_STARTED, OBJECT_TRACK_UPDATED, and OBJECT_TRACK_LOST events."""
        if not self.on_event_callback:
            return

        new_ids = current_ids - self._previous_track_ids
        for t in tracks:
            if t.track_id in new_ids:
                evt = CameraEvent(
                    event_type=EventType.OBJECT_TRACK_STARTED,
                    camera_id=self.camera_id,
                    frame_id=frame_id,
                    track_id=t.track_id,
                    object_type=t.object_type,
                    confidence=t.confidence,
                    message=f"New {t.object_type} track {t.formatted_id} detected with confidence {t.confidence:.2f}"
                )
                self.on_event_callback(evt)

        lost_ids = self._previous_track_ids - current_ids
        for lid in lost_ids:
            evt = CameraEvent(
                event_type=EventType.OBJECT_TRACK_LOST,
                camera_id=self.camera_id,
                frame_id=frame_id,
                track_id=lid,
                message=f"Track ID #{lid} lost / out of view"
            )
            self.on_event_callback(evt)

        self._previous_track_ids = current_ids

    def get_performance_stats(self) -> Dict[str, Any]:
        with self.lock:
            persons = sum(1 for t in self.active_tracks if t.object_type == "person")
            vehicles = sum(1 for t in self.active_tracks if t.object_type == "vehicle")
            return {
                "camera_id": self.camera_id,
                "ai_status": self.status,
                "model_name": self.detector.model_name,
                "inference_fps": self.inference_fps,
                "detector_time_ms": self.last_detector_time_ms,
                "tracker_time_ms": self.last_tracker_time_ms,
                "total_pipeline_ms": self.last_total_pipeline_ms,
                "total_detections": len(self.latest_detections),
                "active_tracks": len(self.active_tracks),
                "persons_count": persons,
                "vehicles_count": vehicles,
                "processed_frames": self.processed_frames,
                "skipped_frames": self.skipped_frames,
                "last_error": self.last_error
            }


class AIPipelineService:
    """
    Central AI Perception Service for IBVAP 2.0.
    Initializes detectors and orchestrates per-camera AI tracking pipelines.
    """

    def __init__(self):
        self.detector: Optional[BaseObjectDetector] = None
        self.pipelines: Dict[str, CameraAIPipeline] = {}
        self.observation_subscribers: List[Callable[[AIObservation], None]] = []
        self._lock = threading.Lock()
        self.is_initialized = False

    def initialize(self):
        """Loads configured detector and establishes pipelines."""
        if self.is_initialized:
            return

        logger.info("Initializing IBVAP 2.0 Edge AI Perception Engine...")
        model_type = settings.AI_DETECTOR_TYPE.lower()

        if model_type == "mock":
            self.detector = MockDetector(
                confidence_threshold=settings.DETECTION_CONFIDENCE,
                iou_threshold=settings.IOU_THRESHOLD,
                device=settings.AI_DEVICE
            )
        elif model_type == "rtdetr":
            self.detector = RTDETRDetector(
                model_path=settings.AI_MODEL_PATH,
                confidence_threshold=settings.DETECTION_CONFIDENCE,
                iou_threshold=settings.IOU_THRESHOLD,
                device=settings.AI_DEVICE
            )
        else:  # default yolo
            self.detector = YOLODetector(
                model_path=settings.AI_MODEL_PATH,
                confidence_threshold=settings.DETECTION_CONFIDENCE,
                iou_threshold=settings.IOU_THRESHOLD,
                device=settings.AI_DEVICE
            )

        success = self.detector.load_model()
        if not success and model_type != "mock":
            logger.warning(f"Failed to load neural model '{settings.AI_MODEL_PATH}'. Falling back to Mock deterministic detector for safety.")
            self.detector = MockDetector(
                confidence_threshold=settings.DETECTION_CONFIDENCE,
                iou_threshold=settings.IOU_THRESHOLD,
                device="cpu"
            )
            self.detector.load_model()

        self.is_initialized = True
        logger.info(f"AI Perception Engine ready with detector: {self.detector.model_name}")

    def register_observation_subscriber(self, callback: Callable[[AIObservation], None]):
        """Subscribes to all structured AI observations (for Phase 3 verification module)."""
        if callback not in self.observation_subscribers:
            self.observation_subscribers.append(callback)

    def _broadcast_observation(self, obs: AIObservation):
        for sub in list(self.observation_subscribers):
            try:
                sub(obs)
            except Exception as e:
                logger.error(f"Observation subscriber error: {e}")

    def process_frame_packet(self, packet: FramePacket):
        """
        Zero-copy frame callback hook registered with Phase 1 CameraManager.
        """
        if not self.is_initialized or not settings.AI_ENABLED:
            return

        cam_id = packet.metadata.camera_id
        with self._lock:
            if cam_id not in self.pipelines:
                self.pipelines[cam_id] = CameraAIPipeline(
                    camera_id=cam_id,
                    detector=self.detector,
                    on_observation_callback=self._broadcast_observation
                )
            pipeline = self.pipelines[cam_id]

        pipeline.enqueue_frame(packet)

    def get_camera_pipeline(self, camera_id: str) -> Optional[CameraAIPipeline]:
        with self._lock:
            return self.pipelines.get(camera_id)

    def remove_camera_pipeline(self, camera_id: str):
        with self._lock:
            pipe = self.pipelines.pop(camera_id, None)
            if pipe:
                pipe.stop()

    def get_camera_tracks(self, camera_id: str) -> List[TrackedObject]:
        pipe = self.get_camera_pipeline(camera_id)
        if not pipe:
            return []
        with pipe.lock:
            return list(pipe.active_tracks)

    def get_camera_detections(self, camera_id: str) -> List[DetectionResult]:
        pipe = self.get_camera_pipeline(camera_id)
        if not pipe:
            return []
        with pipe.lock:
            return list(pipe.latest_detections)

    def get_camera_observations(self, camera_id: str) -> List[AIObservation]:
        pipe = self.get_camera_pipeline(camera_id)
        if not pipe:
            return []
        with pipe.lock:
            return list(pipe.recent_observations)

    def get_camera_performance(self, camera_id: str) -> Dict[str, Any]:
        pipe = self.get_camera_pipeline(camera_id)
        if not pipe:
            return {
                "camera_id": camera_id,
                "ai_status": "STANDBY",
                "model_name": self.detector.model_name if self.detector else "None",
                "inference_fps": 0.0,
                "total_pipeline_ms": 0.0,
                "active_tracks": 0,
                "persons_count": 0,
                "vehicles_count": 0
            }
        return pipe.get_performance_stats()

    def get_annotated_jpeg(self, camera_id: str) -> Optional[bytes]:
        pipe = self.get_camera_pipeline(camera_id)
        if pipe:
            with pipe.lock:
                return pipe.annotated_jpeg
        return None

    def get_global_status(self) -> Dict[str, Any]:
        with self._lock:
            active_pipes = len(self.pipelines)
            total_active_tracks = sum(len(p.active_tracks) for p in self.pipelines.values())
            avg_fps = sum(p.inference_fps for p in self.pipelines.values())

        return {
            "status": "RUNNING" if self.is_initialized and settings.AI_ENABLED else "DISABLED",
            "detector_type": settings.AI_DETECTOR_TYPE,
            "model_name": self.detector.model_name if self.detector else "None",
            "model_info": self.detector.get_model_info() if self.detector else {},
            "device": self.detector._resolved_device if hasattr(self.detector, "_resolved_device") else settings.AI_DEVICE,
            "active_camera_pipelines": active_pipes,
            "total_active_tracks": total_active_tracks,
            "aggregate_inference_fps": round(avg_fps, 1),
            "tracking_algorithm": "ByteTrack",
            "trajectory_history_length": settings.TRAJECTORY_HISTORY_LENGTH
        }


# Global singleton AI perception service
ai_service = AIPipelineService()
