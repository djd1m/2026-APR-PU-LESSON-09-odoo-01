from datetime import datetime, date, timedelta
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestAlerts(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project = self.env["remont.project"].create({
            "name": "Alert Test Project",
            "address": "456 Alert Street",
            "status": "in_progress",
        })
        self.engine = self.env["remont.alert.engine"]

    # ------------------------------------------------------------------
    # Basic model tests
    # ------------------------------------------------------------------

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
        self.assertFalse(alert.cooldown_until)

    def test_alert_types(self):
        """Test all alert types can be created."""
        for alert_type in ["absence", "overbudget", "delay", "camera_error"]:
            alert = self.env["remont.alert"].create({
                "type": alert_type,
                "severity": "info",
                "message": "Test alert: %s" % alert_type,
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

    # ------------------------------------------------------------------
    # Crew absence detection
    # ------------------------------------------------------------------

    def test_crew_absence_alert(self):
        """When no snapshot exists for >24h on a workday, an absence alert
        should be created with cooldown_until set.
        """
        camera = self.env["remont.camera"].create({
            "serial_number": "CAM-ALERT-001",
            "rtsp_url": "rtsp://192.168.1.200:554/stream",
            "project_id": self.project.id,
        })

        # Snapshot 30 hours old
        old_time = datetime.now() - timedelta(hours=30)
        self.env["remont.snapshot"].create({
            "image_url": "test/snapshot.jpg",
            "captured_at": old_time,
            "camera_id": camera.id,
            "project_id": self.project.id,
        })

        # Simulate a workday (Wednesday = weekday 2)
        fake_now = datetime(2026, 5, 27, 10, 0, 0)  # Wednesday
        with patch(
            "odoo.addons.remont_alerts.models.alert_engine.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
            self.engine._check_crew_absence(self.project)

        alerts = self.env["remont.alert"].search([
            ("project_id", "=", self.project.id),
            ("type", "=", "absence"),
        ])
        self.assertTrue(
            len(alerts) >= 1,
            "Absence alert should be created when snapshot is >24h old on workday.",
        )
        self.assertEqual(alerts[0].severity, "warning")
        # Cooldown should be set
        self.assertTrue(alerts[0].cooldown_until)

    # ------------------------------------------------------------------
    # Budget overrun (Decimal)
    # ------------------------------------------------------------------

    def test_budget_overrun_decimal(self):
        """Budget overrun alert must use Decimal arithmetic, not float.
        Setting actual=125% of estimate should create a critical alert.
        """
        self.project.write({
            "budget_estimate": 100000.00,
            "budget_actual": 125000.00,
        })

        self.engine._check_budget_overrun(self.project)

        alerts = self.env["remont.alert"].search([
            ("project_id", "=", self.project.id),
            ("type", "=", "overbudget"),
        ])
        self.assertEqual(
            len(alerts), 1,
            "Overbudget critical alert should be created at >=100%.",
        )
        self.assertEqual(alerts[0].severity, "critical")

    def test_budget_80pct_warning(self):
        """At 81% budget consumption, a warning alert should be created."""
        self.project.write({
            "budget_estimate": 100000.00,
            "budget_actual": 81000.00,
        })

        self.engine._check_budget_overrun(self.project)

        alerts = self.env["remont.alert"].search([
            ("project_id", "=", self.project.id),
            ("type", "=", "overbudget"),
        ])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].severity, "warning")

    def test_no_budget_alert_within_threshold(self):
        """No alert when budget is below 80% threshold."""
        self.project.write({
            "budget_estimate": 100000.00,
            "budget_actual": 70000.00,
        })

        self.engine._check_budget_overrun(self.project)

        alerts = self.env["remont.alert"].search([
            ("project_id", "=", self.project.id),
            ("type", "=", "overbudget"),
        ])
        self.assertEqual(
            len(alerts), 0,
            "No overbudget alert when actual is below 80% threshold.",
        )

    def test_budget_no_duplicate_warning(self):
        """Once a warning alert exists, a second call should not create
        a duplicate warning.
        """
        self.project.write({
            "budget_estimate": 100000.00,
            "budget_actual": 85000.00,
        })

        self.engine._check_budget_overrun(self.project)
        self.engine._check_budget_overrun(self.project)

        alerts = self.env["remont.alert"].search([
            ("project_id", "=", self.project.id),
            ("type", "=", "overbudget"),
        ])
        self.assertEqual(
            len(alerts), 1,
            "Only one warning alert should exist (no duplicates).",
        )

    # ------------------------------------------------------------------
    # Cooldown
    # ------------------------------------------------------------------

    def test_cooldown_prevents_duplicate(self):
        """An alert with cooldown_until in the future should prevent
        a duplicate alert of the same type for the same project.
        """
        # Create an alert with active cooldown
        self.env["remont.alert"].create({
            "type": "absence",
            "severity": "warning",
            "message": "Crew not detected (existing)",
            "project_id": self.project.id,
            "cooldown_until": datetime.now() + timedelta(hours=2),
        })

        camera = self.env["remont.camera"].create({
            "serial_number": "CAM-COOL-001",
            "rtsp_url": "rtsp://192.168.1.201:554/stream",
            "project_id": self.project.id,
        })

        # Snapshot 30 hours old -- would normally trigger an alert
        old_time = datetime.now() - timedelta(hours=30)
        self.env["remont.snapshot"].create({
            "image_url": "test/cooldown_snapshot.jpg",
            "captured_at": old_time,
            "camera_id": camera.id,
            "project_id": self.project.id,
        })

        # Simulate workday
        fake_now = datetime(2026, 5, 27, 10, 0, 0)  # Wednesday
        with patch(
            "odoo.addons.remont_alerts.models.alert_engine.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
            self.engine._check_crew_absence(self.project)

        alerts = self.env["remont.alert"].search([
            ("project_id", "=", self.project.id),
            ("type", "=", "absence"),
        ])
        self.assertEqual(
            len(alerts), 1,
            "Cooldown should prevent duplicate absence alert.",
        )

    # ------------------------------------------------------------------
    # Schedule delay
    # ------------------------------------------------------------------

    def test_schedule_delay_prediction(self):
        """Stage with low progress and tight deadline should trigger
        a delay alert (predicted_delay > 3 days).
        """
        today = date.today()
        self.env["remont.stage"].create({
            "name": "plumbing",
            "project_id": self.project.id,
            "status": "in_progress",
            "progress_pct": 30.0,
            "actual_start": today - timedelta(days=10),
            "planned_end": today + timedelta(days=2),
            "planned_start": today - timedelta(days=10),
        })

        self.engine._check_schedule_delay(self.project)

        alerts = self.env["remont.alert"].search([
            ("project_id", "=", self.project.id),
            ("type", "=", "delay"),
        ])
        # predicted: ((100-30)/30)*10 - 2 = 23.3 - 2 = 21.3 > 3
        self.assertEqual(
            len(alerts), 1,
            "Delay alert should be created when predicted delay > 3 days.",
        )
        self.assertEqual(alerts[0].severity, "warning")
        self.assertIn("plumbing", alerts[0].message)
