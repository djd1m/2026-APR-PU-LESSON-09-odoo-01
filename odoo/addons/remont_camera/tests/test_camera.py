from datetime import datetime, timedelta, date

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestCamera(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project = self.env["remont.project"].create({
            "name": "Test Renovation Project",
            "address": "123 Test Street",
        })

    def test_camera_creation(self):
        """Test basic camera creation with required fields."""
        camera = self.env["remont.camera"].create({
            "serial_number": "CAM-001",
            "rtsp_url": "rtsp://192.168.1.100:554/stream",
            "project_id": self.project.id,
        })
        self.assertEqual(camera.serial_number, "CAM-001")
        self.assertEqual(camera.status, "offline")
        self.assertEqual(camera.project_id, self.project)
        self.assertTrue(camera.installed_at)

    def test_camera_creation_default_capture_interval(self):
        """Test that capture_interval_minutes defaults to 15."""
        camera = self.env["remont.camera"].create({
            "serial_number": "CAM-INTERVAL-001",
            "rtsp_url": "rtsp://192.168.1.100:554/stream",
            "project_id": self.project.id,
        })
        self.assertEqual(camera.capture_interval_minutes, 15)

    def test_camera_serial_unique(self):
        """Test that serial numbers must be unique."""
        self.env["remont.camera"].create({
            "serial_number": "CAM-UNIQUE-001",
            "rtsp_url": "rtsp://192.168.1.101:554/stream",
            "project_id": self.project.id,
        })
        with self.assertRaises(Exception):
            self.env["remont.camera"].create({
                "serial_number": "CAM-UNIQUE-001",
                "rtsp_url": "rtsp://192.168.1.102:554/stream",
                "project_id": self.project.id,
            })

    def test_camera_status_transitions(self):
        """Test camera status can be changed through all valid states."""
        camera = self.env["remont.camera"].create({
            "serial_number": "CAM-002",
            "rtsp_url": "rtsp://192.168.1.103:554/stream",
            "project_id": self.project.id,
        })
        self.assertEqual(camera.status, "offline")

        camera.status = "online"
        self.assertEqual(camera.status, "online")

        camera.status = "error"
        self.assertEqual(camera.status, "error")

        camera.status = "online"
        self.assertEqual(camera.status, "online")

        camera.status = "returned"
        self.assertEqual(camera.status, "returned")

    def test_returned_before_installed_raises(self):
        """Test that returned_at cannot be before installed_at."""
        now = datetime.now()
        with self.assertRaises(ValidationError):
            self.env["remont.camera"].create({
                "serial_number": "CAM-003",
                "rtsp_url": "rtsp://192.168.1.104:554/stream",
                "project_id": self.project.id,
                "installed_at": now,
                "returned_at": now - timedelta(days=1),
            })

    def test_capture_interval_below_minimum_raises(self):
        """Test that capture_interval_minutes < 5 raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.env["remont.camera"].create({
                "serial_number": "CAM-LOW-INTERVAL",
                "rtsp_url": "rtsp://192.168.1.105:554/stream",
                "project_id": self.project.id,
                "capture_interval_minutes": 3,
            })

    def test_capture_interval_above_maximum_raises(self):
        """Test that capture_interval_minutes > 60 raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.env["remont.camera"].create({
                "serial_number": "CAM-HIGH-INTERVAL",
                "rtsp_url": "rtsp://192.168.1.106:554/stream",
                "project_id": self.project.id,
                "capture_interval_minutes": 120,
            })

    def test_capture_interval_valid_boundary(self):
        """Test that capture_interval_minutes at boundaries (5, 60) is accepted."""
        cam_min = self.env["remont.camera"].create({
            "serial_number": "CAM-MIN-INTERVAL",
            "rtsp_url": "rtsp://192.168.1.107:554/stream",
            "project_id": self.project.id,
            "capture_interval_minutes": 5,
        })
        self.assertEqual(cam_min.capture_interval_minutes, 5)

        cam_max = self.env["remont.camera"].create({
            "serial_number": "CAM-MAX-INTERVAL",
            "rtsp_url": "rtsp://192.168.1.108:554/stream",
            "project_id": self.project.id,
            "capture_interval_minutes": 60,
        })
        self.assertEqual(cam_max.capture_interval_minutes, 60)

    def test_max_cameras_per_project(self):
        """Test that a project cannot have more than 4 cameras."""
        for i in range(4):
            self.env["remont.camera"].create({
                "serial_number": f"CAM-LIMIT-{i:03d}",
                "rtsp_url": f"rtsp://192.168.1.{200 + i}:554/stream",
                "project_id": self.project.id,
            })

        with self.assertRaises(ValidationError):
            self.env["remont.camera"].create({
                "serial_number": "CAM-LIMIT-005",
                "rtsp_url": "rtsp://192.168.1.205:554/stream",
                "project_id": self.project.id,
            })

    def test_last_capture_at_initially_empty(self):
        """Test that last_capture_at is not set on creation."""
        camera = self.env["remont.camera"].create({
            "serial_number": "CAM-LASTCAP-001",
            "rtsp_url": "rtsp://192.168.1.110:554/stream",
            "project_id": self.project.id,
        })
        self.assertFalse(camera.last_capture_at)

    def test_snapshot_count_computed(self):
        """Test that snapshot_count is computed from snapshot_ids."""
        camera = self.env["remont.camera"].create({
            "serial_number": "CAM-COUNT-001",
            "rtsp_url": "rtsp://192.168.1.111:554/stream",
            "project_id": self.project.id,
        })
        self.assertEqual(camera.snapshot_count, 0)

        # Create a snapshot linked to this camera
        self.env["remont.snapshot"].create({
            "image_url": "s3://test/snap1.jpg",
            "captured_at": datetime.now(),
            "camera_id": camera.id,
            "project_id": self.project.id,
        })
        camera.invalidate_recordset()
        self.assertEqual(camera.snapshot_count, 1)


class TestTimelapse(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project = self.env["remont.project"].create({
            "name": "Timelapse Test Project",
            "address": "456 Test Avenue",
        })
        self.camera = self.env["remont.camera"].create({
            "serial_number": "CAM-TL-001",
            "rtsp_url": "rtsp://192.168.1.200:554/stream",
            "project_id": self.project.id,
        })

    def test_timelapse_creation(self):
        """Test basic timelapse record creation."""
        timelapse = self.env["remont.timelapse"].create({
            "video_url": "s3://remont-videos/test.mp4",
            "duration_sec": 30,
            "period": "daily",
            "date_from": date(2026, 1, 1),
            "date_to": date(2026, 1, 2),
            "project_id": self.project.id,
            "share_token": "abc123token",
        })
        self.assertEqual(timelapse.period, "daily")
        self.assertEqual(timelapse.duration_sec, 30)
        self.assertEqual(timelapse.share_token, "abc123token")

    def test_timelapse_with_camera_and_frame_count(self):
        """Test timelapse creation with new camera_id and frame_count fields."""
        timelapse = self.env["remont.timelapse"].create({
            "video_url": "s3://remont-videos/test2.mp4",
            "duration_sec": 30,
            "period": "daily",
            "date_from": date(2026, 5, 1),
            "date_to": date(2026, 5, 2),
            "project_id": self.project.id,
            "camera_id": self.camera.id,
            "frame_count": 96,
        })
        self.assertEqual(timelapse.camera_id, self.camera)
        self.assertEqual(timelapse.frame_count, 96)

    def test_timelapse_frame_count_negative_raises(self):
        """Test that negative frame_count raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.env["remont.timelapse"].create({
                "video_url": "s3://remont-videos/bad.mp4",
                "duration_sec": 30,
                "period": "daily",
                "date_from": date(2026, 5, 1),
                "date_to": date(2026, 5, 2),
                "project_id": self.project.id,
                "frame_count": -1,
            })

    def test_timelapse_date_order_validation(self):
        """Test that date_from > date_to raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.env["remont.timelapse"].create({
                "video_url": "s3://remont-videos/bad_dates.mp4",
                "duration_sec": 30,
                "period": "weekly",
                "date_from": date(2026, 5, 10),
                "date_to": date(2026, 5, 1),
                "project_id": self.project.id,
            })


class TestCaptureScheduling(TransactionCase):
    """Tests for the capture scheduling cron logic."""

    def setUp(self):
        super().setUp()
        self.project = self.env["remont.project"].create({
            "name": "Capture Test Project",
            "address": "789 Test Blvd",
        })
        self.camera = self.env["remont.camera"].create({
            "serial_number": "CAM-CRON-001",
            "rtsp_url": "rtsp://192.168.1.50:554/stream",
            "project_id": self.project.id,
            "capture_interval_minutes": 15,
        })
        self.service = self.env["remont.capture.service"]

    def test_cron_skips_offline_camera(self):
        """Test that offline cameras are skipped by the cron."""
        self.camera.status = "offline"
        result = self.service.action_enqueue_capture(self.camera)
        self.assertFalse(result)

    def test_cron_skips_returned_camera(self):
        """Test that returned cameras are skipped by the cron."""
        self.camera.status = "returned"
        result = self.service.action_enqueue_capture(self.camera)
        self.assertFalse(result)
