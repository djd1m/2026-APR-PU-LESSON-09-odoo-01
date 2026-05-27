"""YOLOv8-based renovation stage detector."""

import logging
import os
from io import BytesIO

from minio import Minio
from ultralytics import YOLO

from app.detector_base import BaseDetector, DetectionResult, STAGES

logger = logging.getLogger(__name__)

MODEL_PATH = os.environ.get('CV_MODEL_PATH', 'models/remont_stages_v1.pt')

MODEL_VERSION = os.environ.get(
    'CV_MODEL_VERSION',
    os.path.splitext(os.path.basename(MODEL_PATH))[0],
)


class YOLODetector(BaseDetector):
    """Detect renovation stage using YOLOv8 classification/detection model.

    Runs locally, no API calls. Requires fine-tuned model weights for
    accurate renovation stage classification.
    """

    def __init__(self):
        self.minio_client = Minio(
            os.environ['MINIO_ENDPOINT'].replace('http://', '').replace('https://', ''),
            access_key=os.environ['MINIO_ACCESS_KEY'],
            secret_key=os.environ['MINIO_SECRET_KEY'],
            secure=os.environ.get('MINIO_SECURE', 'false').lower() == 'true',
        )

        if os.path.exists(MODEL_PATH):
            self.model = YOLO(MODEL_PATH)
            logger.info("Loaded YOLOv8 model from %s (version: %s)", MODEL_PATH, MODEL_VERSION)
        else:
            self.model = YOLO('yolov8n-cls.pt')
            logger.warning(
                "Custom model not found at %s, using pretrained. Fine-tune needed.",
                MODEL_PATH,
            )

        self.model_version = MODEL_VERSION

    def detect_stage(self, image_path: str) -> DetectionResult:
        """Detect renovation stage from image stored in MinIO using YOLOv8."""
        try:
            response = self.minio_client.get_object('remont-photos', image_path)
            image_data = BytesIO(response.read())
            response.close()

            results = self.model.predict(image_data, conf=0.3, verbose=False)

            if not results or len(results) == 0:
                return DetectionResult('unknown', 0.0, None, 'yolo')

            result = results[0]

            # Classification model
            if hasattr(result, 'probs') and result.probs is not None:
                top_idx = int(result.probs.top1)
                confidence = float(result.probs.top1conf)
                stage = STAGES[top_idx] if top_idx < len(STAGES) else 'unknown'
                return DetectionResult(stage, confidence, None, 'yolo')

            # Detection model
            if hasattr(result, 'boxes') and result.boxes is not None and len(result.boxes) > 0:
                best = max(result.boxes, key=lambda b: float(b.conf))
                stage_idx = int(best.cls)
                confidence = float(best.conf)
                stage = STAGES[stage_idx] if stage_idx < len(STAGES) else 'unknown'
                return DetectionResult(stage, confidence, None, 'yolo')

            return DetectionResult('unknown', 0.0, None, 'yolo')

        except Exception as e:
            logger.error("YOLOv8 detection failed for %s: %s", image_path, e)
            return DetectionResult('unknown', 0.0, None, 'yolo')
