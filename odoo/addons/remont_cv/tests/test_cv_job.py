"""Tests for the CV Pipeline Odoo integration (remont_cv module)."""

from datetime import datetime
from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestCvJob(TransactionCase):
    """Test remont.cv.job model."""

    def setUp(self):
        super().setUp()
        self.project = self.env["remont.project"].create({
            "name": "CV Test Project",
            "address": "Test Street 1",
        })
        self.camera = self.env["remont.camera"].create({
            "serial_number": "CV-CAM-001",
            "rtsp_url": "rtsp://192.168.1.1:554/stream",
            "project_id": self.project.id,
        })
        self.snapshot = self.env["remont.snapshot"].create({
            "image_url": "projects/1/snapshots/2026-05-27/120000_1.jpg",
            "thumbnail_url": "projects/1/snapshots/2026-05-27/120000_1_thumb.jpg",
            "captured_at": datetime.now(),
            "camera_id": self.camera.id,
            "project_id": self.project.id,
        })

    def test_cv_job_creation(self):
        """CV job is created with correct defaults."""
        job = self.env["remont.cv.job"].create({
            "snapshot_id": self.snapshot.id,
        })
        self.assertEqual(job.status, "queued")
        self.assertFalse(job.stage_result)
        self.assertEqual(job.confidence, 0.0)

    def test_cv_job_status_transitions(self):
        """CV job status transitions: queued → processing → done."""
        job = self.env["remont.cv.job"].create({
            "snapshot_id": self.snapshot.id,
        })
        self.assertEqual(job.status, "queued")

        job.write({"status": "processing"})
        self.assertEqual(job.status, "processing")

        job.write({
            "status": "done",
            "stage_result": "plaster",
            "confidence": 0.85,
            "processed_at": datetime.now(),
        })
        self.assertEqual(job.status, "done")
        self.assertEqual(job.stage_result, "plaster")

    def test_cv_job_failed_status(self):
        """CV job can be marked as failed with error info."""
        job = self.env["remont.cv.job"].create({
            "snapshot_id": self.snapshot.id,
        })
        job.write({
            "status": "failed",
            "stage_result": "unknown",
            "confidence": 0.0,
        })
        self.assertEqual(job.status, "failed")

    def test_needs_manual_review_low_confidence(self):
        """CV job with confidence < 0.65 needs manual review."""
        job = self.env["remont.cv.job"].create({
            "snapshot_id": self.snapshot.id,
            "status": "done",
            "stage_result": "plaster",
            "confidence": 0.45,
        })
        self.assertTrue(job.needs_manual_review)

    def test_needs_manual_review_high_confidence(self):
        """CV job with confidence >= 0.65 does NOT need manual review."""
        job = self.env["remont.cv.job"].create({
            "snapshot_id": self.snapshot.id,
            "status": "done",
            "stage_result": "plaster",
            "confidence": 0.85,
        })
        self.assertFalse(job.needs_manual_review)

    def test_needs_manual_review_queued_status(self):
        """CV job that is not done does NOT need manual review."""
        job = self.env["remont.cv.job"].create({
            "snapshot_id": self.snapshot.id,
            "status": "queued",
            "confidence": 0.0,
        })
        self.assertFalse(job.needs_manual_review)

    def test_valid_stage_results(self):
        """Only valid stage names are accepted."""
        valid_stages = [
            "empty", "demolition", "electrical", "plumbing",
            "plaster", "screed", "tiles", "painting", "finishing", "unknown",
        ]
        for stage in valid_stages:
            job = self.env["remont.cv.job"].create({
                "snapshot_id": self.snapshot.id,
                "stage_result": stage,
            })
            self.assertEqual(job.stage_result, stage)

    def test_model_version_stored(self):
        """Model version is stored with classification result."""
        job = self.env["remont.cv.job"].create({
            "snapshot_id": self.snapshot.id,
            "status": "done",
            "stage_result": "tiles",
            "confidence": 0.92,
            "model_version": "remont_stages_v1",
        })
        self.assertEqual(job.model_version, "remont_stages_v1")


class TestCvMixin(TransactionCase):
    """Test remont.cv.mixin abstract model."""

    def setUp(self):
        super().setUp()
        self.project = self.env["remont.project"].create({
            "name": "Mixin Test Project",
            "address": "Mixin Street 1",
        })
        self.camera = self.env["remont.camera"].create({
            "serial_number": "MIX-CAM-001",
            "rtsp_url": "rtsp://192.168.1.2:554/stream",
            "project_id": self.project.id,
        })
        self.snapshot = self.env["remont.snapshot"].create({
            "image_url": "projects/2/snapshots/2026-05-27/130000_1.jpg",
            "captured_at": datetime.now(),
            "camera_id": self.camera.id,
            "project_id": self.project.id,
        })
        self.mixin = self.env["remont.cv.mixin"]

    def test_confidence_threshold_default(self):
        """Default confidence threshold is 0.65."""
        threshold = self.mixin._get_confidence_threshold()
        self.assertEqual(threshold, 0.65)

    @patch("odoo.addons.remont_cv.models.cv_mixin.redis")
    def test_enqueue_creates_cv_job(self, mock_redis):
        """Enqueuing creates a remont.cv.job record."""
        mock_redis.Redis.return_value = MagicMock()
        job = self.mixin.enqueue_cv_job(self.snapshot)
        self.assertEqual(job.status, "queued")
        self.assertEqual(job.snapshot_id, self.snapshot)

    def test_receive_result_updates_snapshot(self):
        """Receiving CV result updates snapshot stage and confidence."""
        job = self.env["remont.cv.job"].create({
            "snapshot_id": self.snapshot.id,
            "status": "queued",
        })

        self.mixin.receive_cv_result(
            job_id=job.id,
            stage="plaster",
            confidence=0.88,
            model_version="remont_stages_v1",
        )

        job.invalidate_recordset()
        self.snapshot.invalidate_recordset()

        self.assertEqual(job.status, "done")
        self.assertEqual(job.stage_result, "plaster")
        self.assertEqual(self.snapshot.stage_detected, "plaster")

    def test_receive_result_low_confidence_no_stage_update(self):
        """Low confidence result updates snapshot but NOT project stage."""
        # Create a stage for the project
        stage = self.env["remont.stage"].create({
            "name": "plaster",
            "project_id": self.project.id,
            "sequence": 4,
            "progress_pct": 50.0,
        })

        job = self.env["remont.cv.job"].create({
            "snapshot_id": self.snapshot.id,
            "status": "queued",
        })

        self.mixin.receive_cv_result(
            job_id=job.id,
            stage="plaster",
            confidence=0.40,  # Below 0.65 threshold
            model_version="remont_stages_v1",
        )

        stage.invalidate_recordset()
        # Stage progress should NOT have changed
        self.assertEqual(stage.progress_pct, 50.0)
