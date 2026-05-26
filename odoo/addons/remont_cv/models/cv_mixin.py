import json
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CvMixin(models.AbstractModel):
    _name = "remont.cv.mixin"
    _description = "CV Pipeline Mixin"

    def _get_redis_config(self):
        """Get Redis connection parameters from system config."""
        ICP = self.env["ir.config_parameter"].sudo()
        return {
            "host": ICP.get_param("remont_cv.redis_host", "localhost"),
            "port": int(ICP.get_param("remont_cv.redis_port", "6379")),
            "db": int(ICP.get_param("remont_cv.redis_db", "0")),
            "queue_name": ICP.get_param(
                "remont_cv.redis_queue", "cv_jobs"
            ),
        }

    def enqueue_cv_job(self, snapshot):
        """
        Enqueue a CV analysis job to Redis for the given snapshot.

        Creates a remont.cv.job record with status 'queued' and
        pushes the job payload to the Redis queue. The external
        CV worker picks up jobs from this queue.

        :param snapshot: remont.snapshot record
        :returns: remont.cv.job record
        """
        cv_job = self.env["remont.cv.job"].create({
            "snapshot_id": snapshot.id,
            "status": "queued",
        })

        payload = json.dumps({
            "job_id": cv_job.id,
            "snapshot_id": snapshot.id,
            "image_url": snapshot.image_url,
            "project_id": snapshot.project_id.id,
        })

        try:
            import redis
            config = self._get_redis_config()
            r = redis.Redis(
                host=config["host"],
                port=config["port"],
                db=config["db"],
            )
            r.lpush(config["queue_name"], payload)
            _logger.info(
                "CV job %s enqueued for snapshot %s",
                cv_job.id,
                snapshot.id,
            )
        except ImportError:
            _logger.warning(
                "redis package not installed; CV job %s created "
                "but not enqueued",
                cv_job.id,
            )
        except Exception as e:
            _logger.error(
                "Failed to enqueue CV job %s: %s", cv_job.id, e
            )

        return cv_job

    def receive_cv_result(self, job_id, stage_result, confidence):
        """
        Receive a CV result via JSON-RPC and update the job record.

        Called by the external CV worker when processing is complete.

        :param job_id: int - remont.cv.job ID
        :param stage_result: str - detected renovation stage
        :param confidence: float - model confidence (0.0-1.0)
        :returns: bool
        """
        cv_job = self.env["remont.cv.job"].browse(job_id)
        if not cv_job.exists():
            _logger.warning("CV job %s not found", job_id)
            return False

        cv_job.write({
            "status": "done",
            "stage_result": stage_result,
            "confidence": confidence,
            "processed_at": fields.Datetime.now(),
        })

        # Update snapshot with detected stage
        snapshot = cv_job.snapshot_id
        if snapshot.exists():
            snapshot.write({
                "stage_detected": stage_result,
                "cv_confidence": confidence,
            })

        _logger.info(
            "CV job %s completed: stage=%s, confidence=%.2f",
            job_id,
            stage_result,
            confidence,
        )
        return True

    def mark_cv_job_failed(self, job_id, error_message):
        """
        Mark a CV job as failed.

        :param job_id: int - remont.cv.job ID
        :param error_message: str - error details
        :returns: bool
        """
        cv_job = self.env["remont.cv.job"].browse(job_id)
        if not cv_job.exists():
            _logger.warning("CV job %s not found", job_id)
            return False

        cv_job.write({
            "status": "failed",
            "error_message": error_message,
            "processed_at": fields.Datetime.now(),
        })

        _logger.error(
            "CV job %s failed: %s", job_id, error_message
        )
        return True
