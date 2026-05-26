from decimal import Decimal
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestRemontProject(TransactionCase):
    """Tests for the remont.project model."""

    def setUp(self):
        super().setUp()
        self.Project = self.env["remont.project"]
        self.Stage = self.env["remont.stage"]

    def test_create_project(self):
        """Test basic project creation with required fields."""
        project = self.Project.create(
            {
                "name": "Test Apartment Renovation",
                "address": "123 Test Street, Apt 4",
                "area_sqm": 75.5,
                "type": "renovation",
                "status": "draft",
            }
        )
        self.assertTrue(project.id)
        self.assertEqual(project.name, "Test Apartment Renovation")
        self.assertEqual(project.address, "123 Test Street, Apt 4")
        self.assertAlmostEqual(project.area_sqm, 75.5)
        self.assertEqual(project.type, "renovation")
        self.assertEqual(project.status, "draft")

    def test_project_default_status(self):
        """Test that new projects default to draft status."""
        project = self.Project.create({"name": "Draft Project"})
        self.assertEqual(project.status, "draft")

    def test_project_budget_monetary(self):
        """Test that budget fields use Monetary (Decimal-backed) storage."""
        project = self.Project.create(
            {
                "name": "Budget Test Project",
                "budget_estimate": 1500000.50,
                "budget_actual": 1200000.75,
            }
        )
        # Monetary fields in Odoo are stored as float in Python
        # but backed by NUMERIC in PostgreSQL (Decimal precision)
        self.assertAlmostEqual(project.budget_estimate, 1500000.50, places=2)
        self.assertAlmostEqual(project.budget_actual, 1200000.75, places=2)

    def test_project_budget_negative_rejected(self):
        """Test that negative budget values are rejected."""
        with self.assertRaises(ValidationError):
            self.Project.create(
                {
                    "name": "Negative Budget",
                    "budget_estimate": -100.00,
                }
            )

    def test_project_date_validation(self):
        """Test that end date before start date is rejected."""
        with self.assertRaises(ValidationError):
            self.Project.create(
                {
                    "name": "Bad Dates Project",
                    "start_date": "2026-06-01",
                    "end_date_plan": "2026-05-01",
                }
            )

    def test_project_currency(self):
        """Test that currency_id defaults to company currency."""
        project = self.Project.create({"name": "Currency Test"})
        self.assertEqual(project.currency_id, self.env.company.currency_id)


class TestRemontStage(TransactionCase):
    """Tests for the remont.stage model."""

    def setUp(self):
        super().setUp()
        self.Project = self.env["remont.project"]
        self.Stage = self.env["remont.stage"]
        self.project = self.Project.create({"name": "Stage Test Project"})

    def test_create_stage(self):
        """Test basic stage creation."""
        stage = self.Stage.create(
            {
                "name": "demolition",
                "project_id": self.project.id,
                "status": "planned",
            }
        )
        self.assertTrue(stage.id)
        self.assertEqual(stage.name, "demolition")
        self.assertEqual(stage.status, "planned")
        self.assertEqual(stage.project_id.id, self.project.id)

    def test_stage_default_progress(self):
        """Test that new stages start at 0% progress."""
        stage = self.Stage.create(
            {
                "name": "electrical",
                "project_id": self.project.id,
            }
        )
        self.assertAlmostEqual(stage.progress_pct, 0.0)

    def test_stage_progress_validation(self):
        """Test that progress outside 0-100 range is rejected."""
        with self.assertRaises(ValidationError):
            self.Stage.create(
                {
                    "name": "plumbing",
                    "project_id": self.project.id,
                    "progress_pct": 150.0,
                }
            )

        with self.assertRaises(ValidationError):
            self.Stage.create(
                {
                    "name": "plumbing",
                    "project_id": self.project.id,
                    "progress_pct": -10.0,
                }
            )

    def test_stage_linked_to_project(self):
        """Test One2many relationship between project and stages."""
        self.Stage.create(
            {
                "name": "demolition",
                "project_id": self.project.id,
                "sequence": 1,
            }
        )
        self.Stage.create(
            {
                "name": "electrical",
                "project_id": self.project.id,
                "sequence": 2,
            }
        )
        self.assertEqual(len(self.project.stage_ids), 2)

    def test_stage_planned_date_validation(self):
        """Test that planned end before planned start is rejected."""
        with self.assertRaises(ValidationError):
            self.Stage.create(
                {
                    "name": "tiles",
                    "project_id": self.project.id,
                    "planned_start": "2026-07-01",
                    "planned_end": "2026-06-01",
                }
            )
