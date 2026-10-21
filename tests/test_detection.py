"""
Unit tests for Sentinel Detection data models and threshold logic.
"""

import time
import pytest
from backend.detection.fire_detector import Detection, DetectionResult


class TestDetectionModels:
    """Tests for Detection and DetectionResult data structures."""

    def test_detection_initialization(self, sample_detection_data):
        detection = Detection(
            bbox=sample_detection_data["bbox"],
            confidence=sample_detection_data["confidence"],
            class_name=sample_detection_data["class_name"],
            timestamp=sample_detection_data["timestamp"],
        )
        assert detection.confidence == 0.96
        assert detection.class_name == "fire"
        assert len(detection.bbox) == 4

    def test_detection_result_empty(self):
        now = time.time()
        result = DetectionResult(
            frame_id=101,
            timestamp=now,
            detections=[],
            max_confidence=0.0,
            alert_level=None,
        )
        assert result.frame_id == 101
        assert len(result.detections) == 0
        assert result.max_confidence == 0.0
        assert result.alert_level is None

    def test_detection_result_with_detections(self, sample_detection_data):
        now = time.time()
        det1 = Detection(
            bbox=sample_detection_data["bbox"],
            confidence=0.96,
            class_name="fire",
            timestamp=now,
        )
        det2 = Detection(
            bbox=(50, 50, 120, 120),
            confidence=0.74,
            class_name="smoke",
            timestamp=now,
        )
        result = DetectionResult(
            frame_id=102,
            timestamp=now,
            detections=[det1, det2],
            max_confidence=0.96,
            alert_level="P1",
        )
        assert len(result.detections) == 2
        assert result.max_confidence == 0.96
        assert result.alert_level == "P1"
