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

    def _get_confidence_threshold(self):
        """Get confidence threshold from system config."""
        ICP = self.env["ir.config_parameter"].sudo()
        return float(
            ICP.get_param("remont_cv.confidence_threshold", "0.65")
        )

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

    def receive_cv_result(self, job_id, stage_result, confidence,
                          model_version=None):
        """
        Receive a CV result via JSON-RPC and update the job record.

        Called by the external CV worker when processing is complete.

        :param job_id: int - remont.cv.job ID
        :param stage_result: str - detected renovation stage
        :param confidence: float - model confidence (0.0-1.0)
        :param model_version: str - version of the model used
        :returns: bool
        """
        cv_job = self.env["remont.cv.job"].browse(job_id)
        if not cv_job.exists():
            _logger.warning("CV job %s not found", job_id)
            return False

        vals = {
            "status": "done",
            "stage_result": stage_result,
            "confidence": confidence,
            "processed_at": fields.Datetime.now(),
        }
        if model_version:
            vals["model_version"] = model_version

        cv_job.write(vals)

        # Update snapshot with detected stage
        snapshot = cv_job.snapshot_id
        if snapshot.exists():
            snapshot.write({
                "stage_detected": stage_result,
                "cv_confidence": confidence,
            })

        # Update stage progress if confidence meets threshold
        threshold = self._get_confidence_threshold()
        if confidence >= threshold and stage_result not in (
            "unknown", False, None
        ):
            project_id = snapshot.project_id.id if snapshot.exists() else None
            if project_id:
                self._update_stage_progress(project_id, stage_result)

        _logger.info(
            "CV job %s completed: stage=%s, confidence=%.2f, model=%s",
            job_id,
            stage_result,
            confidence,
            model_version or "N/A",
        )
        return True

    def _update_stage_progress(self, project_id, detected_stage):
        """
        Update project stage progress based on recent CV detections.

        Calculates progress as ratio of detections for the dominant
        stage in the last 20 high-confidence snapshots.

        :param project_id: int - remont.project ID
        :param detected_stage: str - detected stage name
        """
        threshold = self._get_confidence_threshold()
        recent = self.env["remont.snapshot"].search_read(
            [
                ("project_id", "=", project_id),
                ("cv_confidence", ">=", threshold),
            ],
            fields=["stage_detected"],
            limit=20,
            order="captured_at desc",
        )

        if not recent:
            return

        stage_counts = {}
        for snap in recent:
            s = snap.get("stage_detected")
            if s:
                stage_counts[s] = stage_counts.get(s, 0) + 1

        if not stage_counts:
            return

        dominant = max(stage_counts, key=stage_counts.get)
        progress = (stage_counts[dominant] / len(recent)) * 100

        if dominant == detected_stage:
            stage_records = self.env["remont.stage"].search([
                ("project_id", "=", project_id),
                ("name", "=", detected_stage),
            ])
            if stage_records:
                stage_records.write({
                    "progress_pct": min(progress, 100),
                    "status": "done" if progress >= 95 else "in_progress",
                })
                _logger.info(
                    "Updated stage %s for project %s: progress=%.0f%%",
                    detected_stage,
                    project_id,
                    progress,
                )

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
