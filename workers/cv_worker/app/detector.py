"""YOLOv8-based renovation stage detector."""

import logging
import os
from io import BytesIO

from minio import Minio
from ultralytics import YOLO

logger = logging.getLogger(__name__)

STAGES = [
    'empty',
    'demolition',
    'electrical',
    'plumbing',
    'plaster',
    'screed',
    'tiles',
    'painting',
    'finishing',
]

# Valid stage names for the 8 renovation stages (excluding 'empty')
VALID_RENOVATION_STAGES = STAGES[1:]  # demolition through finishing

MODEL_PATH = os.environ.get('CV_MODEL_PATH', 'models/remont_stages_v1.pt')

# Extract model version from path or environment
MODEL_VERSION = os.environ.get(
    'CV_MODEL_VERSION',
    os.path.splitext(os.path.basename(MODEL_PATH))[0],
)


class RenovationDetector:
    """Detect renovation stage from construction site images using YOLOv8."""

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
            # Use pretrained model for initial development
            self.model = YOLO('yolov8n-cls.pt')
            logger.warning(
                "Custom model not found at %s, using pretrained. Fine-tune needed.",
                MODEL_PATH,
            )

        self.model_version = MODEL_VERSION

    def detect_stage(self, image_path: str) -> tuple[str, float]:
        """
        Detect renovation stage from image stored in MinIO.

        Args:
            image_path: S3 key in 'remont-photos' bucket

        Returns:
            Tuple of (stage_name, confidence).
            stage_name is one of the 9 STAGES values or 'unknown'.
            confidence is a float between 0.0 and 1.0.
        """
        try:
            # Download image from MinIO
            response = self.minio_client.get_object('remont-photos', image_path)
            image_data = BytesIO(response.read())
            response.close()

            # Run inference
            results = self.model.predict(image_data, conf=0.3, verbose=False)

            if not results or len(results) == 0:
                return 'unknown', 0.0

            result = results[0]

            # For classification model
            if hasattr(result, 'probs') and result.probs is not None:
                top_idx = int(result.probs.top1)
                confidence = float(result.probs.top1conf)
                if top_idx < len(STAGES):
                    return STAGES[top_idx], confidence
                return 'unknown', confidence

            # For detection model
            if hasattr(result, 'boxes') and result.boxes is not None and len(result.boxes) > 0:
                best = max(result.boxes, key=lambda b: float(b.conf))
                stage_idx = int(best.cls)
                confidence = float(best.conf)
                if stage_idx < len(STAGES):
                    return STAGES[stage_idx], confidence

            return 'unknown', 0.0

        except Exception as e:
            logger.error("Stage detection failed for %s: %s", image_path, e)
            return 'unknown', 0.0
