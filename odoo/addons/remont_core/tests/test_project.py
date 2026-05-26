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

    def test_project_status_planning(self):
        """Test that planning status is available in the workflow."""
        project = self.Project.create(
            {"name": "Planning Project", "status": "planning"}
        )
        self.assertEqual(project.status, "planning")

    def test_project_status_on_hold(self):
        """Test that on_hold status is available."""
        project = self.Project.create(
            {"name": "On Hold Project", "status": "on_hold"}
        )
        self.assertEqual(project.status, "on_hold")

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

    def test_project_budget_decimal_precision(self):
        """Test Decimal precision for budget calculations (no float errors)."""
        project = self.Project.create(
            {
                "name": "Decimal Precision Test",
                "budget_estimate": 500000.00,
                "budget_actual": 400000.00,
            }
        )
        # Use Decimal for calculation, never float
        estimate = Decimal(str(project.budget_estimate))
        actual = Decimal(str(project.budget_actual))
        remaining = estimate - actual
        self.assertEqual(remaining, Decimal("100000.00"))

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

    def test_project_overall_progress_empty(self):
        """Test that overall progress is 0 when no stages exist."""
        project = self.Project.create({"name": "No Stages Project"})
        self.assertAlmostEqual(project.overall_progress, 0.0)

    def test_project_overall_progress_computed(self):
        """Test weighted average overall progress calculation."""
        project = self.Project.create({"name": "Progress Test"})
        self.Stage.create(
            {
                "name": "demolition",
                "project_id": project.id,
                "progress_pct": 100.0,
                "weight": 1.0,
            }
        )
        self.Stage.create(
            {
                "name": "electrical",
                "project_id": project.id,
                "progress_pct": 50.0,
                "weight": 1.0,
            }
        )
        self.Stage.create(
            {
                "name": "plumbing",
                "project_id": project.id,
                "progress_pct": 0.0,
                "weight": 1.0,
            }
        )
        # (100*1 + 50*1 + 0*1) / (1+1+1) = 50.0
        self.assertAlmostEqual(project.overall_progress, 50.0, places=1)

    def test_project_overall_progress_weighted(self):
        """Test overall progress respects stage weights."""
        project = self.Project.create({"name": "Weighted Progress"})
        self.Stage.create(
            {
                "name": "demolition",
                "project_id": project.id,
                "progress_pct": 100.0,
                "weight": 2.0,
            }
        )
        self.Stage.create(
            {
                "name": "finishing",
                "project_id": project.id,
                "progress_pct": 0.0,
                "weight": 1.0,
            }
        )
        # (100*2 + 0*1) / (2+1) = 66.67
        self.assertAlmostEqual(project.overall_progress, 66.67, places=1)

    def test_project_with_all_8_stages(self):
        """Test creating a project with all 8 renovation stages."""
        project = self.Project.create({"name": "Full Project"})
        stage_names = [
            "demolition", "electrical", "plumbing", "plaster",
            "screed", "tiles", "painting", "finishing",
        ]
        for i, name in enumerate(stage_names):
            self.Stage.create(
                {
                    "name": name,
                    "project_id": project.id,
                    "sequence": (i + 1) * 10,
                }
            )
        self.assertEqual(len(project.stage_ids), 8)


class TestRemontStage(TransactionCase):
    """Tests for the remont.stage model."""

    def setUp(self):
        super().setUp()
        self.Project = self.env["remont.project"]
        self.Stage = self.env["remont.stage"]
        self.Checklist = self.env["remont.checklist.item"]
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

    def test_stage_default_weight(self):
        """Test that new stages have default weight of 1.0."""
        stage = self.Stage.create(
            {
                "name": "plaster",
                "project_id": self.project.id,
            }
        )
        self.assertAlmostEqual(stage.weight, 1.0)

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

    def test_stage_progress_update(self):
        """Test updating stage progress from 0 to 50 to 100."""
        stage = self.Stage.create(
            {
                "name": "tiles",
                "project_id": self.project.id,
                "progress_pct": 0.0,
                "status": "planned",
            }
        )
        stage.write({"progress_pct": 50.0, "status": "in_progress"})
        self.assertAlmostEqual(stage.progress_pct, 50.0)
        self.assertEqual(stage.status, "in_progress")

        stage.write({"progress_pct": 100.0, "status": "done"})
        self.assertAlmostEqual(stage.progress_pct, 100.0)
        self.assertEqual(stage.status, "done")

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

    def test_stage_dependency_blocks_start(self):
        """Test that a stage cannot start if predecessors are not done."""
        stage_demo = self.Stage.create(
            {
                "name": "demolition",
                "project_id": self.project.id,
                "status": "planned",
            }
        )
        stage_elec = self.Stage.create(
            {
                "name": "electrical",
                "project_id": self.project.id,
                "status": "planned",
                "dependency_ids": [(4, stage_demo.id)],
            }
        )
        # Trying to start electrical while demolition is still planned
        with self.assertRaises(ValidationError):
            stage_elec.write({"status": "in_progress"})

    def test_stage_dependency_allows_start_when_done(self):
        """Test that a stage can start when predecessors are done."""
        stage_demo = self.Stage.create(
            {
                "name": "demolition",
                "project_id": self.project.id,
                "status": "done",
                "progress_pct": 100.0,
            }
        )
        stage_elec = self.Stage.create(
            {
                "name": "electrical",
                "project_id": self.project.id,
                "status": "planned",
                "dependency_ids": [(4, stage_demo.id)],
            }
        )
        # Should not raise
        stage_elec.write({"status": "in_progress"})
        self.assertEqual(stage_elec.status, "in_progress")

    def test_checklist_blocks_stage_completion(self):
        """Test that stage cannot be marked done with unchecked items."""
        stage = self.Stage.create(
            {
                "name": "electrical",
                "project_id": self.project.id,
                "status": "in_progress",
            }
        )
        self.Checklist.create(
            {
                "name": "Wiring done",
                "stage_id": stage.id,
                "is_done": False,
            }
        )
        self.Checklist.create(
            {
                "name": "Outlets installed",
                "stage_id": stage.id,
                "is_done": True,
            }
        )
        with self.assertRaises(ValidationError):
            stage.write({"status": "done"})

    def test_checklist_allows_stage_completion(self):
        """Test that stage can be marked done when all items checked."""
        stage = self.Stage.create(
            {
                "name": "plumbing",
                "project_id": self.project.id,
                "status": "in_progress",
            }
        )
        self.Checklist.create(
            {
                "name": "Pipes installed",
                "stage_id": stage.id,
                "is_done": True,
            }
        )
        self.Checklist.create(
            {
                "name": "Pressure tested",
                "stage_id": stage.id,
                "is_done": True,
            }
        )
        # Should not raise
        stage.write({"status": "done"})
        self.assertEqual(stage.status, "done")

    def test_checklist_progress_computed(self):
        """Test computed checklist progress percentage."""
        stage = self.Stage.create(
            {
                "name": "electrical",
                "project_id": self.project.id,
            }
        )
        self.Checklist.create(
            {"name": "Item 1", "stage_id": stage.id, "is_done": True}
        )
        self.Checklist.create(
            {"name": "Item 2", "stage_id": stage.id, "is_done": True}
        )
        self.Checklist.create(
            {"name": "Item 3", "stage_id": stage.id, "is_done": True}
        )
        self.Checklist.create(
            {"name": "Item 4", "stage_id": stage.id, "is_done": False}
        )
        # 3/4 = 75%
        self.assertAlmostEqual(stage.checklist_progress, 75.0, places=1)


class TestRemontChecklistItem(TransactionCase):
    """Tests for the remont.checklist.item model."""

    def setUp(self):
        super().setUp()
        self.Project = self.env["remont.project"]
        self.Stage = self.env["remont.stage"]
        self.Checklist = self.env["remont.checklist.item"]
        self.project = self.Project.create({"name": "Checklist Project"})
        self.stage = self.Stage.create(
            {
                "name": "electrical",
                "project_id": self.project.id,
            }
        )

    def test_create_checklist_item(self):
        """Test basic checklist item creation."""
        item = self.Checklist.create(
            {
                "name": "Install wiring",
                "stage_id": self.stage.id,
            }
        )
        self.assertTrue(item.id)
        self.assertEqual(item.name, "Install wiring")
        self.assertFalse(item.is_done)
        self.assertFalse(item.completed_by)

    def test_checklist_item_mark_done(self):
        """Test marking a checklist item as done."""
        item = self.Checklist.create(
            {
                "name": "Test outlets",
                "stage_id": self.stage.id,
            }
        )
        item.write({"is_done": True})
        self.assertTrue(item.is_done)

    def test_checklist_item_linked_to_stage(self):
        """Test One2many relationship between stage and checklist items."""
        self.Checklist.create(
            {"name": "Item A", "stage_id": self.stage.id}
        )
        self.Checklist.create(
            {"name": "Item B", "stage_id": self.stage.id}
        )
        self.assertEqual(len(self.stage.checklist_ids), 2)
