"""Tests for remont_timelapse Odoo module."""

from datetime import date, datetime

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestTimelapseJob(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project = self.env["remont.project"].create({
            "name": "Timelapse Test Project",
            "address": "Test Street 42",
            "status": "in_progress",
        })

    def test_job_creation_defaults(self):
        """Timelapse job gets correct defaults: queued status, daily period."""
        job = self.env["remont.timelapse.job"].create({
            "project_id": self.project.id,
        })
        self.assertEqual(job.status, "queued")
        self.assertEqual(job.period, "daily")
        self.assertTrue(job.share_token)
        self.assertEqual(len(job.share_token), 16)

    def test_share_token_unique(self):
        """Each timelapse job gets a unique share token."""
        job1 = self.env["remont.timelapse.job"].create({
            "project_id": self.project.id,
        })
        job2 = self.env["remont.timelapse.job"].create({
            "project_id": self.project.id,
        })
        self.assertNotEqual(job1.share_token, job2.share_token)

    def test_share_token_sql_unique_constraint(self):
        """SQL unique constraint prevents duplicate share tokens."""
        job1 = self.env["remont.timelapse.job"].create({
            "project_id": self.project.id,
            "share_token": "unique_test_token",
        })
        with self.assertRaises(Exception):
            self.env["remont.timelapse.job"].create({
                "project_id": self.project.id,
                "share_token": "unique_test_token",
            })

    def test_negative_frame_count_rejected(self):
        """Negative frame count raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.env["remont.timelapse.job"].create({
                "project_id": self.project.id,
                "frame_count": -1,
            })

    def test_negative_duration_rejected(self):
        """Negative duration raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.env["remont.timelapse.job"].create({
                "project_id": self.project.id,
                "duration_sec": -5,
            })

    def test_job_completion(self):
        """Job can be marked done with video details."""
        job = self.env["remont.timelapse.job"].create({
            "project_id": self.project.id,
        })
        job.write({
            "status": "done",
            "video_url": "projects/1/timelapse/daily_20260527.mp4",
            "frame_count": 96,
            "duration_sec": 30,
            "completed_at": datetime.now(),
        })
        self.assertEqual(job.status, "done")
        self.assertEqual(job.frame_count, 96)

    def test_job_failure(self):
        """Job can be marked failed with error message."""
        job = self.env["remont.timelapse.job"].create({
            "project_id": self.project.id,
        })
        job.write({
            "status": "failed",
            "error_message": "FFmpeg timeout after 300s",
        })
        self.assertEqual(job.status, "failed")
        self.assertEqual(job.error_message, "FFmpeg timeout after 300s")

    def test_cron_enqueue_active_projects(self):
        """Cron creates jobs only for in_progress projects with snapshots."""
        # Create a snapshot so the project qualifies
        camera = self.env["remont.camera"].create({
            "serial_number": "TL-CAM-001",
            "rtsp_url": "rtsp://192.168.1.1:554/stream",
            "project_id": self.project.id,
        })
        self.env["remont.snapshot"].create({
            "image_url": "test/snap.jpg",
            "captured_at": datetime.now(),
            "camera_id": camera.id,
            "project_id": self.project.id,
        })

        # Run cron
        self.env["remont.timelapse.job"]._cron_enqueue_daily_timelapse()

        # Verify job was created
        jobs = self.env["remont.timelapse.job"].search([
            ("project_id", "=", self.project.id),
        ])
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].period, "daily")

    def test_cron_skips_draft_projects(self):
        """Cron does not create jobs for draft projects."""
        self.project.write({"status": "draft"})
        self.env["remont.timelapse.job"]._cron_enqueue_daily_timelapse()
        jobs = self.env["remont.timelapse.job"].search([
            ("project_id", "=", self.project.id),
        ])
        self.assertEqual(len(jobs), 0)

    def test_cron_no_duplicate_daily_jobs(self):
        """Cron does not create duplicate daily jobs for same day."""
        camera = self.env["remont.camera"].create({
            "serial_number": "TL-CAM-002",
            "rtsp_url": "rtsp://192.168.1.2:554/stream",
            "project_id": self.project.id,
        })
        self.env["remont.snapshot"].create({
            "image_url": "test/snap2.jpg",
            "captured_at": datetime.now(),
            "camera_id": camera.id,
            "project_id": self.project.id,
        })

        # Run cron twice
        self.env["remont.timelapse.job"]._cron_enqueue_daily_timelapse()
        self.env["remont.timelapse.job"]._cron_enqueue_daily_timelapse()

        jobs = self.env["remont.timelapse.job"].search([
            ("project_id", "=", self.project.id),
        ])
        self.assertEqual(len(jobs), 1)  # Only one job, no duplicate


class TestTimelapseModel(TransactionCase):
    """Test remont.timelapse model (in remont_camera)."""

    def setUp(self):
        super().setUp()
        self.project = self.env["remont.project"].create({
            "name": "TL Model Test",
            "address": "Test Ave 1",
        })

    def test_timelapse_creation(self):
        """Timelapse record stores video metadata correctly."""
        tl = self.env["remont.timelapse"].create({
            "video_url": "projects/1/timelapse/daily_20260527.mp4",
            "duration_sec": 30,
            "period": "daily",
            "date_from": date(2026, 5, 26),
            "date_to": date(2026, 5, 27),
            "project_id": self.project.id,
            "share_token": "abcdef1234567890",
            "frame_count": 96,
        })
        self.assertEqual(tl.duration_sec, 30)
        self.assertEqual(tl.frame_count, 96)
        self.assertEqual(tl.share_token, "abcdef1234567890")
