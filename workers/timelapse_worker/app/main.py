"""Timelapse Worker — Redis consumer for FFmpeg timelapse generation."""

import json
import logging
import os
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import redis
from minio import Minio

from app.odoo_client import OdooClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Startup validation
REQUIRED_ENV = ['REDIS_URL', 'MINIO_ENDPOINT', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY', 'ODOO_URL', 'ODOO_DB']
for var in REQUIRED_ENV:
    if not os.environ.get(var):
        logger.fatal(f"Required environment variable {var} is not set. Exiting.")
        sys.exit(1)


def _generate_share_token() -> str:
    """Generate a 16-character hex share token."""
    return uuid.uuid4().hex[:16]


def _send_telegram_notification(
    odoo: OdooClient, project_id: int, period: str, s3_key: str,
) -> None:
    """Notify project owner via Telegram that a timelapse is ready."""
    try:
        projects = odoo.execute('remont.project', 'read', [project_id], {'fields': ['name', 'owner_id']})
        if not projects:
            return
        project = projects[0]
        owner_id = project.get('owner_id')
        if not owner_id:
            return
        # owner_id is [id, name] tuple from Odoo
        if isinstance(owner_id, (list, tuple)):
            owner_id = owner_id[0]
        owners = odoo.execute('res.users', 'read', [owner_id], {'fields': ['telegram_id']})
        if not owners:
            return
        telegram_id = owners[0].get('telegram_id')
        if not telegram_id:
            logger.info(f"Project {project_id}: owner has no telegram_id, skipping notification")
            return

        period_label = "за день" if period == "daily" else "за неделю"
        message = f"Таймлапс ремонта {period_label}: {project.get('name', '')}"
        logger.info(f"Telegram notification queued for chat_id={telegram_id}: {message}")
        # Telegram send is handled by a separate notification service via Redis
        # We enqueue the notification for async delivery
        redis_client = redis.from_url(os.environ['REDIS_URL'])
        redis_client.lpush('telegram_notifications', json.dumps({
            'chat_id': telegram_id,
            'message': message,
            'video_path': s3_key,
        }))
    except Exception as e:
        logger.warning(f"Failed to send Telegram notification for project {project_id}: {e}")


def generate_timelapse(project_id: int, period: str, minio_client: Minio, odoo: OdooClient):
    """Generate timelapse video from project snapshots."""
    now = datetime.utcnow()

    if period == 'daily':
        date_from = (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    elif period == 'weekly':
        date_from = (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    else:
        date_from = (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')

    date_to = now.strftime('%Y-%m-%d %H:%M:%S')

    # Fetch snapshot URLs from Odoo
    snapshots = odoo.execute('remont.snapshot', 'search_read', [
        ('project_id', '=', project_id),
        ('captured_at', '>=', date_from),
        ('captured_at', '<', date_to),
    ], {'order': 'captured_at asc', 'fields': ['image_url']})

    if len(snapshots) < 10:
        logger.info(f"Project {project_id}: only {len(snapshots)} snapshots, skipping timelapse")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        # Download images
        for i, snap in enumerate(snapshots):
            try:
                response = minio_client.get_object('remont-photos', snap['image_url'])
                frame_path = Path(temp_dir) / f"frame_{i:05d}.jpg"
                with open(frame_path, 'wb') as f:
                    f.write(response.read())
                response.close()
            except Exception as e:
                logger.warning(f"Failed to download {snap['image_url']}: {e}")

        # Count downloaded frames
        frames = sorted(Path(temp_dir).glob('frame_*.jpg'))
        if len(frames) < 10:
            logger.info(f"Project {project_id}: only {len(frames)} downloaded frames, skipping")
            return

        # Calculate FPS for ~30 second video
        target_duration = 30
        fps = max(1, len(frames) // target_duration)

        output_path = Path(temp_dir) / 'timelapse.mp4'

        # Generate timelapse with FFmpeg
        cmd = [
            'ffmpeg', '-y',
            '-framerate', str(fps),
            '-i', str(Path(temp_dir) / 'frame_%05d.jpg'),
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"FFmpeg failed: {result.stderr}")
            return

        # Upload to MinIO
        date_str = now.strftime('%Y%m%d')
        s3_key = f"projects/{project_id}/timelapse/{period}_{date_str}.mp4"

        with open(output_path, 'rb') as f:
            file_size = output_path.stat().st_size
            minio_client.put_object('remont-videos', s3_key, f, file_size, content_type='video/mp4')

        logger.info(f"Uploaded timelapse: {s3_key} ({file_size} bytes)")

        # Create share token
        share_token = _generate_share_token()

        # Get video duration via ffprobe
        probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                     '-of', 'default=noprint_wrappers=1:nokey=1', str(output_path)]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        duration = int(float(probe_result.stdout.strip())) if probe_result.returncode == 0 else 30

        # Create timelapse record in Odoo
        odoo.execute('remont.timelapse', 'create', {
            'video_url': s3_key,
            'duration_sec': duration,
            'frame_count': len(frames),
            'period': period,
            'date_from': date_from[:10],
            'date_to': date_to[:10],
            'project_id': project_id,
            'share_token': share_token,
        })

        logger.info(
            f"Timelapse created for project {project_id}: {s3_key} "
            f"(frames={len(frames)}, duration={duration}s, token={share_token})"
        )

        # Notify project owner via Telegram
        _send_telegram_notification(odoo, project_id, period, s3_key)


def main():
    """Main loop: consume timelapse jobs from Redis queue."""
    redis_client = redis.from_url(os.environ['REDIS_URL'])
    minio_client = Minio(
        os.environ['MINIO_ENDPOINT'].replace('http://', '').replace('https://', ''),
        access_key=os.environ['MINIO_ACCESS_KEY'],
        secret_key=os.environ['MINIO_SECRET_KEY'],
        secure=os.environ.get('MINIO_SECURE', 'false').lower() == 'true',
    )
    odoo = OdooClient(
        url=os.environ['ODOO_URL'],
        db=os.environ['ODOO_DB'],
        username=os.environ.get('ODOO_USERNAME', 'admin'),
        password=os.environ.get('ODOO_PASSWORD', 'admin'),
    )

    logger.info("Timelapse Worker started. Waiting for jobs on queue 'timelapse_generate'...")

    while True:
        try:
            result = redis_client.brpop('timelapse_generate', timeout=5)
            if result is None:
                continue

            _, raw_job = result
            job = json.loads(raw_job)
            logger.info(f"Processing timelapse job: project_id={job['project_id']}, period={job['period']}")

            generate_timelapse(job['project_id'], job['period'], minio_client, odoo)

        except Exception as e:
            logger.error(f"Error processing timelapse job: {e}", exc_info=True)
            time.sleep(1)


if __name__ == '__main__':
    main()
