from decimal import Decimal

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestRemontBudget(TransactionCase):
    """Tests for the remont.budget and remont.budget.line models."""

    def setUp(self):
        super().setUp()
        self.Budget = self.env["remont.budget"]
        self.BudgetLine = self.env["remont.budget.line"]
        self.Project = self.env["remont.project"]
        self.project = self.Project.create({"name": "Budget Test Project"})

    def _create_budget_with_lines(self):
        """Helper: create a budget with two line items."""
        budget = self.Budget.create(
            {
                "project_id": self.project.id,
                "version": 1,
                "is_original": True,
                "status": "draft",
            }
        )
        self.BudgetLine.create(
            {
                "budget_id": budget.id,
                "category": "materials",
                "description": "Paint and plaster",
                "estimate_amount": 150000.00,
                "actual_amount": 120000.00,
            }
        )
        self.BudgetLine.create(
            {
                "budget_id": budget.id,
                "category": "labor",
                "description": "Workers",
                "estimate_amount": 350000.00,
                "actual_amount": 340000.00,
            }
        )
        return budget

    # ------------------------------------------------------------------
    # AC-BT-01: All monetary fields use fields.Monetary
    # ------------------------------------------------------------------
    def test_budget_uses_monetary(self):
        """Verify that budget and line monetary fields are fields.Monetary."""
        budget_fields = self.Budget.fields_get(
            ["total_estimate", "total_actual"]
        )
        for fname in ("total_estimate", "total_actual"):
            self.assertEqual(
                budget_fields[fname]["type"],
                "monetary",
                f"Budget.{fname} must be fields.Monetary",
            )

        line_fields = self.BudgetLine.fields_get(
            ["estimate_amount", "actual_amount", "variance"]
        )
        for fname in ("estimate_amount", "actual_amount", "variance"):
            self.assertEqual(
                line_fields[fname]["type"],
                "monetary",
                f"BudgetLine.{fname} must be fields.Monetary",
            )

    # ------------------------------------------------------------------
    # AC-BT-02: Decimal precision — 0.10 + 0.20 == 0.30
    # ------------------------------------------------------------------
    def test_budget_decimal_precision(self):
        """Decimal('0.10') + Decimal('0.20') must equal Decimal('0.30').

        This verifies that budget calculations use Decimal arithmetic
        and do not suffer from IEEE 754 float imprecision.
        """
        budget = self.Budget.create(
            {
                "project_id": self.project.id,
                "version": 1,
                "is_original": True,
                "status": "draft",
            }
        )
        self.BudgetLine.create(
            {
                "budget_id": budget.id,
                "category": "materials",
                "description": "Item A",
                "estimate_amount": 0.10,
                "actual_amount": 0.0,
            }
        )
        self.BudgetLine.create(
            {
                "budget_id": budget.id,
                "category": "labor",
                "description": "Item B",
                "estimate_amount": 0.20,
                "actual_amount": 0.0,
            }
        )
        budget.invalidate_recordset()
        # The total must be exactly 0.30, not 0.30000000000000004
        result = Decimal(str(budget.total_estimate))
        self.assertEqual(
            result,
            Decimal("0.30"),
            f"Expected Decimal('0.30'), got {result}. Float arithmetic detected!",
        )

    # ------------------------------------------------------------------
    # AC-BT-05: _check_overrun returns correct percentage
    # ------------------------------------------------------------------
    def test_budget_overrun_calculation(self):
        """_check_overrun() returns overrun percentage using Decimal."""
        budget = self._create_budget_with_lines()
        budget.invalidate_recordset()

        overrun_pct = budget._check_overrun()

        # total_estimate = 500000, total_actual = 460000 → 92%
        self.assertIsInstance(overrun_pct, Decimal)
        self.assertEqual(overrun_pct, Decimal("92.00000000000000000000000000"))
        # Simpler check with rounding
        self.assertAlmostEqual(float(overrun_pct), 92.0, places=2)

    def test_budget_overrun_zero_estimate(self):
        """_check_overrun() returns 0 when estimate is zero."""
        budget = self.Budget.create(
            {
                "project_id": self.project.id,
                "version": 1,
                "is_original": True,
                "status": "draft",
            }
        )
        result = budget._check_overrun()
        self.assertEqual(result, Decimal("0"))

    # ------------------------------------------------------------------
    # AC-BT-04: Original budget immutable after approval
    # ------------------------------------------------------------------
    def test_original_budget_immutable(self):
        """Original approved budget cannot have estimate_amount modified."""
        budget = self._create_budget_with_lines()
        budget.action_approve()

        line = budget.line_ids[0]

        # Changing estimate_amount on original approved budget must fail
        with self.assertRaises(ValidationError):
            line.write({"estimate_amount": 999999.00})

        # Changing actual_amount should still work
        line.write({"actual_amount": 160000.00})
        self.assertAlmostEqual(line.actual_amount, 160000.00, places=2)

    def test_original_budget_cannot_revert_to_draft(self):
        """Original approved budget cannot revert to draft."""
        budget = self._create_budget_with_lines()
        budget.action_approve()

        with self.assertRaises(ValidationError):
            budget.write({"status": "draft"})

    def test_budget_can_be_locked(self):
        """Approved budget can be locked."""
        budget = self._create_budget_with_lines()
        budget.action_approve()
        budget.action_lock()
        self.assertEqual(budget.status, "locked")

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------
    def test_budget_totals_computed(self):
        """Total estimate and actual are sum of line items."""
        budget = self._create_budget_with_lines()
        budget.invalidate_recordset()

        self.assertAlmostEqual(budget.total_estimate, 500000.00, places=2)
        self.assertAlmostEqual(budget.total_actual, 460000.00, places=2)

    def test_variance_computed(self):
        """Variance = actual - estimate per line."""
        budget = self._create_budget_with_lines()
        materials_line = budget.line_ids.filtered(
            lambda l: l.category == "materials"
        )
        # actual 120000 - estimate 150000 = -30000
        self.assertAlmostEqual(materials_line.variance, -30000.00, places=2)

    # ------------------------------------------------------------------
    # Constraint: amounts must be non-negative
    # ------------------------------------------------------------------
    def test_negative_estimate_rejected(self):
        """Negative estimate_amount is rejected."""
        budget = self.Budget.create(
            {
                "project_id": self.project.id,
                "version": 1,
                "is_original": True,
                "status": "draft",
            }
        )
        with self.assertRaises(ValidationError):
            self.BudgetLine.create(
                {
                    "budget_id": budget.id,
                    "category": "materials",
                    "description": "Bad amount",
                    "estimate_amount": -100.00,
                }
            )
