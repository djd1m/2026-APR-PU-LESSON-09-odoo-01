"""CV Worker — Redis consumer for YOLOv8 renovation stage detection."""

import json
import logging
import os
import sys
import time

import redis

from app.detector import RenovationDetector
from app.odoo_client import OdooClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Startup validation
REQUIRED_ENV = ['REDIS_URL', 'MINIO_ENDPOINT', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY', 'ODOO_URL', 'ODOO_DB']
for var in REQUIRED_ENV:
    if not os.environ.get(var):
        logger.fatal(f"Required environment variable {var} is not set. Exiting.")
        sys.exit(1)


def main():
    """Main loop: consume CV jobs from Redis queue."""
    redis_client = redis.from_url(os.environ['REDIS_URL'])
    detector = RenovationDetector()
    odoo = OdooClient(
        url=os.environ['ODOO_URL'],
        db=os.environ['ODOO_DB'],
        username=os.environ.get('ODOO_USERNAME', 'admin'),
        password=os.environ.get('ODOO_PASSWORD', 'admin'),
    )

    logger.info("CV Worker started. Waiting for jobs on queue 'cv_analyze'...")

    while True:
        try:
            # Blocking pop from Redis queue (timeout 5s)
            result = redis_client.brpop('cv_analyze', timeout=5)
            if result is None:
                continue

            _, raw_job = result
            job = json.loads(raw_job)
            logger.info(f"Processing CV job: snapshot_id={job['snapshot_id']}")

            # Detect stage
            stage, confidence = detector.detect_stage(job['image_path'])
            logger.info(f"Detected stage={stage}, confidence={confidence:.2f}")

            # Update Odoo via JSON-RPC
            odoo.update_snapshot(job['snapshot_id'], stage, confidence)

            if confidence >= 0.7 and stage != 'unknown':
                odoo.update_stage_progress(job['project_id'], stage)

        except Exception as e:
            logger.error(f"Error processing CV job: {e}", exc_info=True)
            time.sleep(1)


if __name__ == '__main__':
    main()
