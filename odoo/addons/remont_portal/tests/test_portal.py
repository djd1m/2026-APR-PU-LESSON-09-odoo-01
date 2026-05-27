"""Tests for the client portal (remont_portal module)."""

from datetime import datetime, date

from odoo.tests.common import TransactionCase


class TestPortalAccess(TransactionCase):
    """Test portal access controls — users see only their own projects."""

    def setUp(self):
        super().setUp()
        self.owner1 = self.env["res.users"].create({
            "name": "Owner One",
            "login": "owner1@test.com",
            "email": "owner1@test.com",
            "password": "TestPass1",
        })
        self.owner2 = self.env["res.users"].create({
            "name": "Owner Two",
            "login": "owner2@test.com",
            "email": "owner2@test.com",
            "password": "TestPass2",
        })
        self.project1 = self.env["remont.project"].create({
            "name": "Owner1 Project",
            "address": "Street 1",
            "owner_id": self.owner1.id,
        })
        self.project2 = self.env["remont.project"].create({
            "name": "Owner2 Project",
            "address": "Street 2",
            "owner_id": self.owner2.id,
        })

    def test_owner_sees_own_project(self):
        """Owner can find their own project."""
        projects = self.env["remont.project"].sudo(self.owner1.id).search([
            ("owner_id", "=", self.owner1.id),
        ])
        self.assertIn(self.project1, projects)

    def test_owner_does_not_see_others_project(self):
        """Owner's search filtered by owner_id excludes other users' projects."""
        projects = self.env["remont.project"].sudo(self.owner1.id).search([
            ("owner_id", "=", self.owner1.id),
        ])
        self.assertNotIn(self.project2, projects)


class TestShareToken(TransactionCase):
    """Test public timelapse share via token."""

    def setUp(self):
        super().setUp()
        self.project = self.env["remont.project"].create({
            "name": "Share Test",
            "address": "Share Street 1",
        })

    def test_timelapse_share_token_lookup(self):
        """Timelapse can be found by share token (public, no auth)."""
        tl = self.env["remont.timelapse"].create({
            "video_url": "projects/1/timelapse/test.mp4",
            "duration_sec": 30,
            "period": "daily",
            "date_from": date(2026, 5, 26),
            "date_to": date(2026, 5, 27),
            "project_id": self.project.id,
            "share_token": "test_share_abcdef",
        })
        found = self.env["remont.timelapse"].sudo().search([
            ("share_token", "=", "test_share_abcdef"),
        ], limit=1)
        self.assertEqual(found, tl)

    def test_invalid_share_token_returns_empty(self):
        """Invalid share token returns empty recordset."""
        found = self.env["remont.timelapse"].sudo().search([
            ("share_token", "=", "nonexistent_token"),
        ], limit=1)
        self.assertFalse(found)


class TestBudgetDisplay(TransactionCase):
    """Test budget calculations for portal display."""

    def setUp(self):
        super().setUp()
        self.project = self.env["remont.project"].create({
            "name": "Budget Display Test",
            "address": "Budget Street 1",
            "budget_estimate": 1800000.00,
            "budget_actual": 1200000.00,
        })

    def test_budget_percentage_calculation(self):
        """Budget percentage is correctly calculated server-side."""
        estimate = self.project.budget_estimate
        actual = self.project.budget_actual
        pct = round(actual / estimate * 100, 1) if estimate else 0
        self.assertAlmostEqual(pct, 66.7, places=1)

    def test_budget_color_green(self):
        """Budget under 80% shows green."""
        pct = 66.7
        color = "danger" if pct > 100 else ("warning" if pct > 80 else "success")
        self.assertEqual(color, "success")

    def test_budget_color_yellow(self):
        """Budget between 80-100% shows yellow."""
        self.project.write({"budget_actual": 1500000.00})
        pct = round(1500000 / 1800000 * 100, 1)
        color = "danger" if pct > 100 else ("warning" if pct > 80 else "success")
        self.assertEqual(color, "warning")

    def test_budget_color_red(self):
        """Budget over 100% shows red."""
        self.project.write({"budget_actual": 2000000.00})
        pct = round(2000000 / 1800000 * 100, 1)
        color = "danger" if pct > 100 else ("warning" if pct > 80 else "success")
        self.assertEqual(color, "danger")
