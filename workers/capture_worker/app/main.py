"""Capture Worker — grabs frames from RTSP cameras and stores in MinIO.

This is the missing link in the pipeline:
  Odoo cron → Redis "camera_capture" → THIS WORKER → MinIO (JPEG) → Redis "cv_jobs"

The worker:
1. Consumes jobs from Redis queue "camera_capture"
2. Connects to camera RTSP stream via FFmpeg
3. Grabs a single frame (JPEG)
4. Generates a thumbnail (320px wide)
5. Uploads both to MinIO
6. Creates a snapshot record in Odoo via JSON-RPC
7. Enqueues a CV analysis job to Redis "cv_jobs"
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import redis
from minio import Minio

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Startup validation
REQUIRED_ENV = ['REDIS_URL', 'MINIO_ENDPOINT', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY', 'ODOO_URL', 'ODOO_DB']
missing = [var for var in REQUIRED_ENV if not os.environ.get(var)]
if missing:
    logger.fatal("Missing required environment variables: %s", ', '.join(missing))
    sys.exit(1)

# Queue names
CAPTURE_QUEUE = os.environ.get('CAPTURE_QUEUE', 'camera_capture')
CV_QUEUE = os.environ.get('CV_QUEUE', 'cv_jobs')

# MinIO bucket
PHOTO_BUCKET = os.environ.get('MINIO_PHOTO_BUCKET', 'remont-photos')

# FFmpeg timeout for RTSP grab
FFMPEG_TIMEOUT = int(os.environ.get('FFMPEG_TIMEOUT', '30'))


def _init_minio() -> Minio:
    endpoint = os.environ['MINIO_ENDPOINT'].replace('http://', '').replace('https://', '')
    return Minio(
        endpoint,
        access_key=os.environ['MINIO_ACCESS_KEY'],
        secret_key=os.environ['MINIO_SECRET_KEY'],
        secure=os.environ.get('MINIO_SECURE', 'false').lower() == 'true',
    )


def _ensure_bucket(minio_client: Minio):
    """Create the photo bucket if it doesn't exist."""
    if not minio_client.bucket_exists(PHOTO_BUCKET):
        minio_client.make_bucket(PHOTO_BUCKET)
        logger.info("Created MinIO bucket: %s", PHOTO_BUCKET)


def _grab_frame(rtsp_url: str, output_path: str) -> bool:
    """Use FFmpeg to grab a single frame from an RTSP stream.

    Args:
        rtsp_url: RTSP stream URL (e.g., rtsp://user:pass@192.168.1.100:554/stream)
        output_path: Local path to write the JPEG frame

    Returns:
        True if frame was captured successfully, False otherwise.
    """
    cmd = [
        'ffmpeg', '-y',
        '-rtsp_transport', 'tcp',
        '-i', rtsp_url,
        '-frames:v', '1',
        '-q:v', '2',       # JPEG quality (2 = high quality)
        '-vf', 'scale=1920:-1',  # Resize to 1920px width, keep aspect ratio
        output_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=FFMPEG_TIMEOUT,
        )
        if result.returncode != 0:
            logger.error("FFmpeg failed (rc=%d): %s", result.returncode, result.stderr.decode()[-500:])
            return False

        # Verify output file exists and is not empty
        if not Path(output_path).exists() or Path(output_path).stat().st_size < 1000:
            logger.error("FFmpeg produced empty or tiny output file")
            return False

        return True
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg timed out after %ds for URL: %s", FFMPEG_TIMEOUT, rtsp_url[:50])
        return False
    except FileNotFoundError:
        logger.fatal("FFmpeg not found. Install it: apt-get install ffmpeg")
        sys.exit(1)


def _create_thumbnail(source_path: str, thumb_path: str) -> bool:
    """Create a 320px wide thumbnail from the source image."""
    cmd = [
        'ffmpeg', '-y',
        '-i', source_path,
        '-vf', 'scale=320:-1',
        '-q:v', '4',
        thumb_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False


def _create_odoo_snapshot(job: dict, s3_path: str, thumb_path: str) -> int | None:
    """Create snapshot record in Odoo via JSON-RPC.

    Returns snapshot ID or None on failure.
    """
    import xmlrpc.client

    url = os.environ['ODOO_URL'].rstrip('/')
    db = os.environ['ODOO_DB']
    username = os.environ.get('ODOO_USERNAME', 'admin')
    password = os.environ.get('ODOO_PASSWORD', 'admin')

    try:
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        if not uid:
            logger.error("Odoo authentication failed")
            return None

        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        snapshot_id = models.execute_kw(db, uid, password, 'remont.snapshot', 'create', [{
            'image_url': s3_path,
            'thumbnail_url': thumb_path,
            'captured_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'camera_id': job['camera_id'],
            'project_id': job['project_id'],
        }])
        return snapshot_id
    except Exception as e:
        logger.error("Failed to create Odoo snapshot: %s", e)
        return None


def process_capture_job(job: dict, minio_client: Minio, redis_client: redis.Redis):
    """Process a single camera capture job.

    Pipeline:
      1. FFmpeg grabs frame from RTSP → temp JPEG
      2. Generate thumbnail
      3. Upload both to MinIO
      4. Create snapshot in Odoo
      5. Enqueue CV analysis job
    """
    camera_id = job['camera_id']
    project_id = job['project_id']
    rtsp_url = job['rtsp_url']
    serial = job.get('serial_number', f'cam-{camera_id}')

    logger.info("Capturing from camera %s (project %d)", serial, project_id)

    with tempfile.TemporaryDirectory() as tmpdir:
        frame_path = os.path.join(tmpdir, 'frame.jpg')
        thumb_local = os.path.join(tmpdir, 'thumb.jpg')

        # Step 1: Grab frame from RTSP
        if not _grab_frame(rtsp_url, frame_path):
            logger.error("Failed to capture frame from camera %s", serial)
            # TODO: update camera status to 'error' via Odoo RPC
            return

        # Step 2: Create thumbnail
        _create_thumbnail(frame_path, thumb_local)

        # Step 3: Upload to MinIO
        now = datetime.utcnow()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H%M%S')
        s3_path = f"projects/{project_id}/snapshots/{date_str}/{time_str}_{camera_id}.jpg"
        s3_thumb = f"projects/{project_id}/snapshots/{date_str}/{time_str}_{camera_id}_thumb.jpg"

        minio_client.fput_object(PHOTO_BUCKET, s3_path, frame_path, content_type='image/jpeg')

        if Path(thumb_local).exists():
            minio_client.fput_object(PHOTO_BUCKET, s3_thumb, thumb_local, content_type='image/jpeg')
        else:
            s3_thumb = s3_path  # fallback: use full image as thumb

        logger.info("Uploaded snapshot: %s (%d bytes)", s3_path, Path(frame_path).stat().st_size)

        # Step 4: Create snapshot record in Odoo
        snapshot_id = _create_odoo_snapshot(job, s3_path, s3_thumb)
        if not snapshot_id:
            logger.error("Failed to create snapshot in Odoo — CV job not enqueued")
            return

        # Step 5: Enqueue CV analysis job
        cv_job = {
            'snapshot_id': snapshot_id,
            'image_path': s3_path,
            'project_id': project_id,
        }
        redis_client.lpush(CV_QUEUE, json.dumps(cv_job))
        logger.info("Enqueued CV job for snapshot %d (camera %s)", snapshot_id, serial)


def main():
    """Main loop: consume capture jobs from Redis queue."""
    redis_client = redis.from_url(os.environ['REDIS_URL'])
    minio_client = _init_minio()
    _ensure_bucket(minio_client)

    logger.info(
        "Capture Worker started. Queue=%s → photos → %s → CV queue=%s",
        CAPTURE_QUEUE, PHOTO_BUCKET, CV_QUEUE,
    )

    while True:
        try:
            result = redis_client.brpop(CAPTURE_QUEUE, timeout=5)
            if result is None:
                continue

            _, raw_job = result
            job = json.loads(raw_job)
            process_capture_job(job, minio_client, redis_client)

        except json.JSONDecodeError as e:
            logger.error("Invalid job payload: %s", e)
        except Exception as e:
            logger.error("Error processing capture job: %s", e, exc_info=True)
            time.sleep(1)


if __name__ == '__main__':
    main()
