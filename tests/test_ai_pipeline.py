import pytest
import numpy as np
from datetime import datetime, timezone

from ai.preprocessing.frame_preprocessor import LowLightPreprocessor, IdentityPreprocessor
from ai.detection.mock_detector import MockDetector
from backend.services.ai_pipeline import CameraAIPipeline, AIPipelineService
from backend.models.frame import FrameMetadata, FramePacket
from ai.schemas.observation import AIObservation


def test_low_light_preprocessor_clahe():
    """Test: LowLightPreprocessor enhances contrast on low-light frames while preserving shape and dtype."""
    preprocessor = LowLightPreprocessor(clip_limit=2.0)
    dark_frame = np.full((720, 1280, 3), 30, dtype=np.uint8)
    enhanced = preprocessor.preprocess(dark_frame)

    assert enhanced.shape == dark_frame.shape
    assert enhanced.dtype == np.uint8
    assert isinstance(enhanced, np.ndarray)


def test_camera_ai_pipeline_end_to_end():
    """
    Test: Raw FramePacket passes through CameraAIPipeline producing detections, active tracks, and AIObservations.
    """
    detector = MockDetector(confidence_threshold=0.35)
    detector.load_model()

    observations = []
    def on_obs(obs: AIObservation):
        observations.append(obs)

    pipeline = CameraAIPipeline(
        camera_id="CAM-PIPELINE-TEST",
        detector=detector,
        on_observation_callback=on_obs
    )

    frame_raw = np.zeros((720, 1280, 3), dtype=np.uint8)
    metadata = FrameMetadata(
        camera_id="CAM-PIPELINE-TEST",
        frame_id=1,
        width=1280,
        height=720,
        fps=25.0
    )
    packet = FramePacket(metadata=metadata, frame=frame_raw)

    pipeline.process_frame(packet)

    assert pipeline.status == "RUNNING"
    assert len(pipeline.latest_detections) >= 2
    assert len(pipeline.active_tracks) >= 2
    assert len(observations) >= 2

    # Validate Observation schema
    obs = observations[0]
    assert obs.camera_id == "CAM-PIPELINE-TEST"
    assert obs.frame_id == 1
    assert obs.object.track_id > 0
    assert obs.object.type in ("person", "vehicle")
    assert len(obs.trajectory) >= 1
    assert pipeline.annotated_jpeg is not None


def test_ai_pipeline_fault_isolation():
    """
    Test: If detector fails/throws an exception, pipeline gracefully catches it, sets status to ERROR,
    and does NOT propagate exception to the ingestion layer.
    """
    class BrokenDetector(MockDetector):
        def detect(self, frame):
            raise RuntimeError("Simulated GPU out of memory error in detector")

    broken = BrokenDetector()
    broken.load_model()

    pipeline = CameraAIPipeline(camera_id="CAM-BROKEN", detector=broken)

    frame_raw = np.zeros((720, 1280, 3), dtype=np.uint8)
    metadata = FrameMetadata(camera_id="CAM-BROKEN", frame_id=1, width=1280, height=720)
    packet = FramePacket(metadata=metadata, frame=frame_raw)

    # Must NOT raise exception
    pipeline.process_frame(packet)
    assert pipeline.status == "ERROR"
    assert "Simulated GPU out of memory" in pipeline.last_error
