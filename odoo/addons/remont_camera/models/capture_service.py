import json
import logging
from datetime import timedelta

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CaptureService(models.AbstractModel):
    """Service model for camera snapshot capture scheduling.

    This model provides methods to enqueue capture jobs to Redis
    for processing by the external FFmpeg-based capture worker.
    It does NOT perform the actual RTSP frame extraction -- that
    is handled by the ``workers/cv_worker`` Docker container.
    """

    _name = "remont.capture.service"
    _description = "Camera Capture Scheduling Service"

    def _get_redis_connection(self):
        """Return a Redis connection for job enqueue.

        Returns None if Redis is not configured or unavailable,
        allowing graceful degradation during development.
        """
        try:
            import redis
            redis_url = self.env["ir.config_parameter"].sudo().get_param(
                "remont.redis_url", default="redis://localhost:6379/0"
            )
            return redis.from_url(redis_url)
        except Exception:
            _logger.warning("Redis connection unavailable. Capture jobs will not be enqueued.")
            return None

    def action_enqueue_capture(self, camera):
        """Enqueue a single capture job to the Redis queue.

        Args:
            camera: ``remont.camera`` recordset (single record).

        The job payload contains all information the FFmpeg worker needs
        to pull a frame from the RTSP stream and store it in MinIO.
        """
        camera.ensure_one()

        if camera.status != "active":
            _logger.info(
                "Skipping capture for camera %s (status=%s)",
                camera.serial_number,
                camera.status,
            )
            return False

        job_payload = {
            "camera_id": camera.id,
            "project_id": camera.project_id.id,
            "serial_number": camera.serial_number,
            "rtsp_url": camera.rtsp_url,
        }

        conn = self._get_redis_connection()
        if conn is not None:
            try:
                conn.rpush("camera_capture", json.dumps(job_payload))
                camera.write({"last_capture_at": fields.Datetime.now()})
                _logger.info(
                    "Enqueued capture job for camera %s (project %s)",
                    camera.serial_number,
                    camera.project_id.name,
                )
                return True
            except Exception as exc:
                _logger.error(
                    "Failed to enqueue capture for camera %s: %s",
                    camera.serial_number,
                    exc,
                )
                return False
        else:
            _logger.warning(
                "Redis unavailable -- capture job for camera %s not enqueued.",
                camera.serial_number,
            )
            return False

    @api.model
    def _cron_capture_all_active(self):
        """Cron method: iterate all active cameras and enqueue captures
        for those whose capture interval has elapsed since last_capture_at.

        This method is designed to be called by an ``ir.cron`` record
        (e.g., every 5 minutes). It checks each camera's individual
        ``capture_interval_minutes`` to decide whether a new capture
        is due.
        """
        cameras = self.env["remont.camera"].search([
            ("status", "=", "active"),
        ])

        now = fields.Datetime.now()
        enqueued = 0

        for camera in cameras:
            if camera.last_capture_at:
                next_due = camera.last_capture_at + timedelta(
                    minutes=camera.capture_interval_minutes
                )
                if now < next_due:
                    continue  # not yet due

            if self.action_enqueue_capture(camera):
                enqueued += 1

        _logger.info(
            "Capture cron complete: %d jobs enqueued out of %d active cameras.",
            enqueued,
            len(cameras),
        )
        return enqueued
