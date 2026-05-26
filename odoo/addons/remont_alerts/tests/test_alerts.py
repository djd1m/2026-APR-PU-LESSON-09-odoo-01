from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase


class TestAlerts(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project = self.env["remont.project"].create({
            "name": "Alert Test Project",
            "address": "456 Alert Street",
            "status": "in_progress",
        })

    def test_alert_creation(self):
        """Test basic alert record creation."""
        alert = self.env["remont.alert"].create({
            "type": "absence",
            "severity": "warning",
            "message": "Crew not detected for 30 hours",
            "project_id": self.project.id,
        })
        self.assertEqual(alert.type, "absence")
        self.assertEqual(alert.severity, "warning")
        self.assertFalse(alert.is_read)
        self.assertTrue(alert.created_at)

    def test_alert_types(self):
        """Test all alert types can be created."""
        for alert_type in ["absence", "overbudget", "delay", "camera_error"]:
            alert = self.env["remont.alert"].create({
                "type": alert_type,
                "severity": "info",
                "message": f"Test alert: {alert_type}",
                "project_id": self.project.id,
            })
            self.assertEqual(alert.type, alert_type)

    def test_alert_mark_read(self):
        """Test marking alert as read."""
        alert = self.env["remont.alert"].create({
            "type": "delay",
            "severity": "critical",
            "message": "Schedule delay detected",
            "project_id": self.project.id,
        })
        self.assertFalse(alert.is_read)
        alert.is_read = True
        self.assertTrue(alert.is_read)

    def test_crew_absence_detection(self):
        """Test crew absence alert engine logic.

        When no snapshot exists for >24h on a workday, an alert should be created.
        """
        engine = self.env["remont.alert.engine"]

        # Create a camera for the project
        camera = self.env["remont.camera"].create({
            "serial_number": "CAM-ALERT-001",
            "rtsp_url": "rtsp://192.168.1.200:554/stream",
            "project_id": self.project.id,
        })

        # Create a snapshot that is 30 hours old
        old_time = datetime.now() - timedelta(hours=30)
        self.env["remont.snapshot"].create({
            "image_url": "test/snapshot.jpg",
            "captured_at": old_time,
            "camera_id": camera.id,
            "project_id": self.project.id,
        })

        # Run absence check
        engine._check_crew_absence(self.project)

        # Check if on a workday - alert should be created
        if datetime.now().weekday() < 5:
            alerts = self.env["remont.alert"].search([
                ("project_id", "=", self.project.id),
                ("type", "=", "absence"),
            ])
            self.assertTrue(
                len(alerts) >= 1,
                "Absence alert should be created when snapshot is >24h old on workday.",
            )

    def test_budget_overrun_detection(self):
        """Test budget overrun alert using Decimal arithmetic."""
        engine = self.env["remont.alert.engine"]

        # Set budget: actual = 120% of estimate (>110% threshold)
        self.project.write({
            "budget_estimate": 100000.00,
            "budget_actual": 125000.00,
        })

        engine._check_budget_overrun(self.project)

        alerts = self.env["remont.alert"].search([
            ("project_id", "=", self.project.id),
            ("type", "=", "overbudget"),
        ])
        self.assertEqual(
            len(alerts),
            1,
            "Overbudget alert should be created when actual > 110% of estimate.",
        )
        self.assertEqual(alerts[0].severity, "critical")

    def test_no_budget_alert_within_threshold(self):
        """No alert when budget is within 110% threshold."""
        engine = self.env["remont.alert.engine"]

        # Set budget: actual = 105% of estimate (within threshold)
        self.project.write({
            "budget_estimate": 100000.00,
            "budget_actual": 105000.00,
        })

        engine._check_budget_overrun(self.project)

        alerts = self.env["remont.alert"].search([
            ("project_id", "=", self.project.id),
            ("type", "=", "overbudget"),
        ])
        self.assertEqual(
            len(alerts),
            0,
            "No overbudget alert should be created when actual is within 110% threshold.",
        )
