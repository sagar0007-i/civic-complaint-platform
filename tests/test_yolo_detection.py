"""Unit Tests for YOLO Pothole Detection Service and Vision Pipeline."""

import io
import pytest
from PIL import Image
from backend.services.yolo_service import (
    YOLOPotholeDetector,
    PotholeDetectionBox,
    PotholeDetectionResult,
)
from backend.services.ai_service import AIService


def _create_sample_image_bytes(width: int = 200, height: int = 200, color: str = "gray") -> bytes:
    """Helper to generate mock image bytes."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_yolo_pothole_box_area_calculation():
    """Test bounding box area calculation."""
    box = PotholeDetectionBox(x1=10, y1=10, x2=60, y2=80, confidence=0.88)
    assert box.box_area == (60 - 10) * (80 - 10)  # 50 * 70 = 3500


def test_yolo_pothole_severity_computation():
    """Test severity calculation based on pothole counts and areas."""
    detector = YOLOPotholeDetector()

    # 0 potholes -> MEDIUM
    assert detector._compute_severity(count=0, total_box_area=0, img_area=10000, max_conf=0.0) == "MEDIUM"

    # 1 small pothole -> HIGH
    assert detector._compute_severity(count=1, total_box_area=500, img_area=10000, max_conf=0.7) == "HIGH"

    # Multiple potholes or large road crater -> CRITICAL
    assert detector._compute_severity(count=3, total_box_area=2500, img_area=10000, max_conf=0.92) == "CRITICAL"


def test_yolo_detection_graceful_fallback_without_weights():
    """Test YOLO detector handles missing weights gracefully without crashing."""
    detector = YOLOPotholeDetector(model_path="ai_models/non_existent_weights.pt")
    img_bytes = _create_sample_image_bytes()

    result = detector.detect_potholes(img_bytes)
    assert isinstance(result, PotholeDetectionResult)
    assert result.potholes_detected is False
    assert result.annotated_image_bytes is not None
    assert "not found" in result.message.lower()


def test_yolo_draw_annotations():
    """Test annotation drawing on PIL images."""
    detector = YOLOPotholeDetector()
    img = Image.new("RGB", (300, 300), color="blue")
    boxes = [
        PotholeDetectionBox(x1=20, y1=30, x2=100, y2=120, confidence=0.91),
        PotholeDetectionBox(x1=150, y1=160, x2=240, y2=250, confidence=0.84),
    ]

    annotated_bytes = detector._draw_annotations(img, boxes)
    assert isinstance(annotated_bytes, bytes)
    assert len(annotated_bytes) > 0

    # Verify returned bytes are valid image data
    loaded_img = Image.open(io.BytesIO(annotated_bytes))
    assert loaded_img.size == (300, 300)


def test_ai_service_integrates_vision():
    """Test AIService.get_suggestions includes vision detection outputs."""
    ai = AIService()
    sample_img = _create_sample_image_bytes()

    sugg = ai.get_suggestions(
        title="Road problem",
        description="There is road damage near signal.",
        landmark="Near Signal",
        image_bytes=sample_img,
    )

    assert "vision" in sugg
    assert "potholes_detected" in sugg["vision"]
    assert "pothole_count" in sugg["vision"]
