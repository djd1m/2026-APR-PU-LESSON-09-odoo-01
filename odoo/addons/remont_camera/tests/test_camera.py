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
        self.assertEqual(camera.status, "active")
        self.assertEqual(camera.project_id, self.project)
        self.assertTrue(camera.installed_at)

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
        """Test camera status can be changed."""
        camera = self.env["remont.camera"].create({
            "serial_number": "CAM-002",
            "rtsp_url": "rtsp://192.168.1.103:554/stream",
            "project_id": self.project.id,
        })
        camera.status = "maintenance"
        self.assertEqual(camera.status, "maintenance")

        camera.status = "inactive"
        self.assertEqual(camera.status, "inactive")

    def test_returned_before_installed_raises(self):
        """Test that returned_at cannot be before installed_at."""
        from datetime import datetime, timedelta

        now = datetime.now()
        with self.assertRaises(ValidationError):
            self.env["remont.camera"].create({
                "serial_number": "CAM-003",
                "rtsp_url": "rtsp://192.168.1.104:554/stream",
                "project_id": self.project.id,
                "installed_at": now,
                "returned_at": now - timedelta(days=1),
            })

    def test_timelapse_creation(self):
        """Test basic timelapse record creation."""
        from datetime import date

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
