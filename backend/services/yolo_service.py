"""YOLO Vision Service for automated civic pothole and road hazard detection."""

import io
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

from backend.config import settings
from backend.utils.logging import logger


class PotholeDetectionBox(BaseModel):
    """Bounding box coordinates and confidence score for a detected pothole."""
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    label: str = "pothole"

    @property
    def box_area(self) -> float:
        """Calculate width * height of the bounding box."""
        return max(0.0, self.x2 - self.x1) * max(0.0, self.y2 - self.y1)


class PotholeDetectionResult(BaseModel):
    """Structured detection outcome from YOLO pothole analysis."""
    potholes_detected: bool = False
    pothole_count: int = 0
    max_confidence: float = 0.0
    boxes: List[PotholeDetectionBox] = Field(default_factory=list)
    annotated_image_bytes: Optional[bytes] = None
    suggested_severity: str = "MEDIUM"
    suggested_category_slug: Optional[str] = None
    model_used: str = "heuristic"
    is_loaded: bool = False
    message: str = ""


class YOLOPotholeDetector:
    """
    Production-ready YOLO Pothole Detection Service.
    Supports PyTorch (.pt) weights and ONNX models exported from Ultralytics / Colab.
    Provides automated fallback if model weights or PyTorch are not yet configured.
    """

    _instance: Optional["YOLOPotholeDetector"] = None
    _model: Any = None
    _model_loaded: bool = False
    _last_error_message: str = ""

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(YOLOPotholeDetector, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.YOLO_POTHOLE_MODEL_PATH
        self.confidence_threshold = settings.YOLO_CONFIDENCE_THRESHOLD
        self.iou_threshold = settings.YOLO_IOU_THRESHOLD

    def is_model_available(self) -> bool:
        """Check if model weight file exists on disk."""
        return bool(self.model_path and os.path.isfile(self.model_path))

    def _get_or_load_model(self) -> Any:
        """Lazily load the YOLO model weights on first inference call."""
        if self._model is not None:
            return self._model

        if not self.is_model_available():
            self._last_error_message = f"YOLO model weights file (pothole_yolo.pt) not found at '{self.model_path}'."
            logger.info(self._last_error_message)
            return None

        try:
            from ultralytics import YOLO

            logger.info(f"Loading YOLO Pothole Detection weights from: {self.model_path}")
            self._model = YOLO(self.model_path)
            self._model_loaded = True
            self._last_error_message = ""
            logger.info("YOLO Pothole Detection model loaded successfully.")
            return self._model
        except ImportError:
            self._last_error_message = "Python package 'ultralytics' is not installed. Run `pip install ultralytics` to enable YOLO vision inference."
            logger.warning(self._last_error_message)
            return None
        except Exception as e:
            self._last_error_message = f"Failed to load YOLO model: {e}"
            logger.error(self._last_error_message, exc_info=True)
            return None

    def detect_potholes(
        self,
        image_input: Union[bytes, Image.Image, str, Path],
        confidence_threshold: Optional[float] = None,
    ) -> PotholeDetectionResult:
        """
        Run pothole detection on the provided image.

        Args:
            image_input: Image bytes, PIL Image, or file path.
            confidence_threshold: Optional override for detection confidence threshold.

        Returns:
            PotholeDetectionResult with detection counts, bounding boxes, and annotated image bytes.
        """
        conf = confidence_threshold or self.confidence_threshold

        # 1. Load and parse PIL Image
        pil_image: Optional[Image.Image] = None
        raw_bytes: Optional[bytes] = None

        try:
            if isinstance(image_input, (bytes, bytearray)):
                raw_bytes = bytes(image_input)
                pil_image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            elif isinstance(image_input, Image.Image):
                pil_image = image_input.convert("RGB")
                buf = io.BytesIO()
                pil_image.save(buf, format="JPEG", quality=90)
                raw_bytes = buf.getvalue()
            elif isinstance(image_input, (str, Path)):
                pil_image = Image.open(str(image_input)).convert("RGB")
                with open(str(image_input), "rb") as f:
                    raw_bytes = f.read()
        except Exception as e:
            logger.warning(f"Unable to decode image for YOLO detection: {e}")
            return PotholeDetectionResult(
                potholes_detected=False,
                message=f"Invalid image format: {e}",
            )

        if pil_image is None:
            return PotholeDetectionResult(potholes_detected=False, message="No image provided")

        img_width, img_height = pil_image.size
        img_area = float(img_width * img_height)

        # 2. Check for loaded model
        model = self._get_or_load_model()

        if model is None:
            # Fallback when weights file or library is missing
            err_msg = self._last_error_message or "YOLO model weights file (pothole_yolo.pt) not found."
            return PotholeDetectionResult(
                potholes_detected=False,
                pothole_count=0,
                max_confidence=0.0,
                boxes=[],
                annotated_image_bytes=raw_bytes,
                suggested_severity="MEDIUM",
                suggested_category_slug=None,
                model_used="none",
                is_loaded=False,
                message=err_msg,
            )

        # 3. Run Inference with Ultralytics YOLO
        try:
            results = model.predict(
                source=pil_image,
                conf=conf,
                iou=self.iou_threshold,
                verbose=False,
            )

            boxes: List[PotholeDetectionBox] = []
            max_conf = 0.0
            total_box_area = 0.0

            if results and len(results) > 0:
                first_res = results[0]
                # Ultralytics results.boxes: xyxy, conf, cls
                if hasattr(first_res, "boxes") and first_res.boxes is not None:
                    xyxy_arr = first_res.boxes.xyxy.cpu().numpy()
                    conf_arr = first_res.boxes.conf.cpu().numpy()
                    cls_arr = first_res.boxes.cls.cpu().numpy()

                    names_dict = getattr(first_res, "names", {0: "pothole"})

                    for i in range(len(xyxy_arr)):
                        box_coords = xyxy_arr[i]
                        box_conf = float(conf_arr[i])
                        cls_id = int(cls_arr[i])
                        raw_label = str(names_dict.get(cls_id, "pothole"))
                        label = "pothole" if raw_label.isdigit() else raw_label

                        p_box = PotholeDetectionBox(
                            x1=float(box_coords[0]),
                            y1=float(box_coords[1]),
                            x2=float(box_coords[2]),
                            y2=float(box_coords[3]),
                            confidence=round(box_conf, 3),
                            label=label,
                        )
                        boxes.append(p_box)
                        total_box_area += p_box.box_area
                        if box_conf > max_conf:
                            max_conf = box_conf

            pothole_count = len(boxes)
            potholes_detected = pothole_count > 0

            # 4. Generate annotated preview image
            annotated_bytes = self._draw_annotations(pil_image, boxes)

            # 5. Compute suggested severity
            suggested_severity = self._compute_severity(pothole_count, total_box_area, img_area, max_conf)

            return PotholeDetectionResult(
                potholes_detected=potholes_detected,
                pothole_count=pothole_count,
                max_confidence=round(max_conf, 2),
                boxes=boxes,
                annotated_image_bytes=annotated_bytes,
                suggested_severity=suggested_severity,
                suggested_category_slug="pothole" if potholes_detected else None,
                model_used="ultralytics_yolo",
                is_loaded=True,
                message=f"Detected {pothole_count} pothole(s)" if potholes_detected else "No potholes detected",
            )

        except Exception as e:
            logger.error(f"YOLO pothole inference error: {e}", exc_info=True)
            return PotholeDetectionResult(
                potholes_detected=False,
                annotated_image_bytes=raw_bytes,
                model_used="error",
                message=f"Inference error: {e}",
            )

    def _compute_severity(
        self,
        count: int,
        total_box_area: float,
        img_area: float,
        max_conf: float,
    ) -> str:
        """Estimate complaint severity based on number and relative size of potholes."""
        if count == 0:
            return "MEDIUM"

        area_ratio = total_box_area / max(img_area, 1.0)

        # Severe danger: multiple deep potholes or huge road crater taking >20% of frame
        if count >= 3 or area_ratio > 0.20 or (count >= 2 and max_conf >= 0.85):
            return "CRITICAL"
        elif count >= 1 or area_ratio > 0.08:
            return "HIGH"
        return "MEDIUM"

    def _draw_annotations(
        self,
        image: Image.Image,
        boxes: List[PotholeDetectionBox],
    ) -> bytes:
        """Draw clean bounding boxes and detection badges on the PIL image."""
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy, "RGBA")

        for box in boxes:
            # Box color: Red/Orange for potholes
            box_outline = "#EF4444"  # Red
            fill_overlay = (239, 68, 68, 45)  # Semi-transparent red highlight

            # 1. Fill highlight inside box
            draw.rectangle(
                [(box.x1, box.y1), (box.x2, box.y2)],
                fill=fill_overlay,
                outline=box_outline,
                width=3,
            )

            # 2. Label tag
            label_text = f"POTHOLE {int(box.confidence * 100)}%"
            text_x = max(box.x1, 0)
            text_y = max(box.y1 - 22, 0)

            # Text background badge
            draw.rectangle(
                [(text_x, text_y), (text_x + 120, text_y + 20)],
                fill="#EF4444",
            )
            draw.text((text_x + 6, text_y + 3), label_text, fill="#FFFFFF")

        out_buf = io.BytesIO()
        img_copy.save(out_buf, format="JPEG", quality=92)
        return out_buf.getvalue()
