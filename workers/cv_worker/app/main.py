"""CV Worker — Redis consumer for renovation stage detection.

Supports two backends (selected via CV_BACKEND env var):
  - yolo: YOLOv8 local inference (requires fine-tuned model)
  - vllm: Vision Language Model via OpenAI-compatible API (zero-shot)
"""

import json
import logging
import os
import sys
import time

import redis

from app.detector_base import BaseDetector
from app.odoo_client import OdooClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Startup validation
REQUIRED_ENV = ['REDIS_URL', 'MINIO_ENDPOINT', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY', 'ODOO_URL', 'ODOO_DB']
for var in REQUIRED_ENV:
    if not os.environ.get(var):
        logger.fatal("Required environment variable %s is not set. Exiting.", var)
        sys.exit(1)

# Backend selection
CV_BACKEND = os.environ.get('CV_BACKEND', 'yolo')

# Confidence threshold
CONFIDENCE_THRESHOLD = float(os.environ.get('CV_CONFIDENCE_THRESHOLD', '0.65'))

# Queue name
QUEUE_NAME = os.environ.get('CV_QUEUE_NAME', 'cv_jobs')


def create_detector() -> BaseDetector:
    """Factory: create detector based on CV_BACKEND environment variable.

    Returns:
        BaseDetector instance (YOLODetector or VLLMDetector).

    Raises:
        SystemExit: if CV_BACKEND is invalid or required env vars missing.
    """
    if CV_BACKEND == 'yolo':
        from app.detector import YOLODetector
        return YOLODetector()
    elif CV_BACKEND == 'vllm':
        from app.detector_vllm import VLLMDetector
        return VLLMDetector()
    else:
        logger.fatal("Unknown CV_BACKEND: '%s'. Must be 'yolo' or 'vllm'.", CV_BACKEND)
        sys.exit(1)


def main():
    """Main loop: consume CV jobs from Redis queue."""
    redis_client = redis.from_url(os.environ['REDIS_URL'])
    detector = create_detector()
    odoo = OdooClient(
        url=os.environ['ODOO_URL'],
        db=os.environ['ODOO_DB'],
        username=os.environ.get('ODOO_USERNAME', 'admin'),
        password=os.environ.get('ODOO_PASSWORD', 'admin'),
    )

    logger.info(
        "CV Worker started. backend=%s, queue=%s, threshold=%.2f. Waiting for jobs...",
        CV_BACKEND, QUEUE_NAME, CONFIDENCE_THRESHOLD,
    )

    while True:
        try:
            result = redis_client.brpop(QUEUE_NAME, timeout=5)
            if result is None:
                continue

            _, raw_job = result
            job = json.loads(raw_job)
            logger.info("Processing CV job: snapshot_id=%s", job['snapshot_id'])

            # Detect stage (returns DetectionResult regardless of backend)
            detection = detector.detect_stage(job['image_path'])
            logger.info(
                "Detected: stage=%s, confidence=%.2f, backend=%s",
                detection.stage, detection.confidence, detection.backend,
            )

            # Update Odoo via JSON-RPC
            odoo.update_snapshot(
                snapshot_id=job['snapshot_id'],
                stage=detection.stage,
                confidence=detection.confidence,
                model_version=detection.backend,
                explanation=detection.explanation,
            )

            if detection.confidence >= CONFIDENCE_THRESHOLD and detection.stage != 'unknown':
                odoo.update_stage_progress(job['project_id'], detection.stage)

        except Exception as e:
            logger.error("Error processing CV job: %s", e, exc_info=True)
            time.sleep(1)


if __name__ == '__main__':
    main()
