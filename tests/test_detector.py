import pytest
import numpy as np
from ai.detection.base_detector import BaseObjectDetector
from ai.detection.yolo_detector import YOLODetector
from ai.detection.mock_detector import MockDetector
from backend.models.detection import DetectionResult


def test_mock_detector_person_and_vehicle_detections():
    """Test: Mock detector produces normalized person and vehicle detections with correct bbox and center."""
    detector = MockDetector(confidence_threshold=0.35)
    assert detector.load_model() is True
    assert detector.is_loaded is True

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    dets = detector.detect(frame)
    assert len(dets) >= 2

    # Verify person detection
    person_dets = [d for d in dets if d.object_type == "person"]
    assert len(person_dets) == 1
    p = person_dets[0]
    assert p.class_name == "person"
    assert p.confidence > 0.35
    assert len(p.bbox) == 4
    assert p.x1 < p.x2 and p.y1 < p.y2
    assert p.center[0] == pytest.approx((p.x1 + p.x2) / 2.0, rel=1e-2)

    # Verify vehicle detection
    veh_dets = [d for d in dets if d.object_type == "vehicle"]
    assert len(veh_dets) == 1
    v = veh_dets[0]
    assert v.class_name in ("car", "motorcycle", "bus", "truck")
    assert v.subclass == "car"


def test_detector_confidence_threshold_filtering():
    """Test: Detections below confidence threshold are filtered out."""
    detector = MockDetector(confidence_threshold=0.95)  # Very high threshold
    detector.load_model()
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    dets = detector.detect(frame)
    assert len(dets) == 0


def test_yolo_detector_invalid_path_handling():
    """Test: Invalid model path fails gracefully without crashing the process."""
    detector = YOLODetector(model_path="non_existent_model_weights_123.pt")
    success = detector.load_model()
    assert success is False
    assert detector.is_loaded is False

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    dets = detector.detect(frame)
    assert dets == []
