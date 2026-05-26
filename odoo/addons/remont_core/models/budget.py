from decimal import Decimal

from odoo import models, fields, api
from odoo.exceptions import ValidationError


BUDGET_STATUSES = [
    ("draft", "Draft"),
    ("approved", "Approved"),
    ("locked", "Locked"),
]

BUDGET_LINE_CATEGORIES = [
    ("materials", "Materials"),
    ("labor", "Labor"),
    ("equipment", "Equipment"),
    ("overhead", "Overhead"),
    ("other", "Other"),
]


class RemontBudget(models.Model):
    _name = "remont.budget"
    _description = "Renovation Budget"
    _order = "version desc"

    project_id = fields.Many2one(
        "remont.project",
        string="Project",
        required=True,
        ondelete="cascade",
    )
    version = fields.Integer(
        string="Version",
        default=1,
        required=True,
    )
    status = fields.Selection(
        selection=BUDGET_STATUSES,
        string="Status",
        default="draft",
        tracking=True,
    )
    is_original = fields.Boolean(
        string="Is Original",
        default=True,
        help="True for the first budget version (version=1).",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    total_estimate = fields.Monetary(
        string="Total Estimate",
        currency_field="currency_id",
        compute="_compute_totals",
        store=True,
    )
    total_actual = fields.Monetary(
        string="Total Actual",
        currency_field="currency_id",
        compute="_compute_totals",
        store=True,
    )
    line_ids = fields.One2many(
        "remont.budget.line",
        "budget_id",
        string="Budget Lines",
    )

    @api.depends(
        "line_ids.estimate_amount",
        "line_ids.actual_amount",
    )
    def _compute_totals(self):
        for budget in self:
            # Use Decimal for all monetary arithmetic — NEVER float
            estimate_total = Decimal("0.00")
            actual_total = Decimal("0.00")
            for line in budget.line_ids:
                estimate_total += Decimal(str(line.estimate_amount or 0))
                actual_total += Decimal(str(line.actual_amount or 0))
            budget.total_estimate = float(estimate_total)
            budget.total_actual = float(actual_total)

    @api.constrains("is_original", "status")
    def _check_original_immutable(self):
        """Original budget (v1) cannot have its structure modified after approval."""
        # Constraint is checked on write — see write() override below.
        pass

    def write(self, vals):
        for record in self:
            if record.is_original and record.status == "approved":
                # Only allow changing actual_amount on lines and status to locked
                forbidden = set(vals.keys()) - {"status", "line_ids"}
                if forbidden:
                    raise ValidationError(
                        "Original approved budget cannot be modified. "
                        "Create a new version instead."
                    )
                if "status" in vals and vals["status"] not in ("approved", "locked"):
                    raise ValidationError(
                        "Original approved budget can only be locked, "
                        "not reverted to draft."
                    )
        return super().write(vals)

    def _check_overrun(self):
        """Compare total_actual vs total_estimate using Decimal arithmetic.

        Returns:
            Decimal: overrun percentage (e.g., Decimal('85.00') means 85% consumed).
                     Returns Decimal('0') if total_estimate is zero.
        """
        self.ensure_one()
        estimate = Decimal(str(self.total_estimate or 0))
        actual = Decimal(str(self.total_actual or 0))

        if estimate == Decimal("0"):
            return Decimal("0")

        return (actual / estimate) * Decimal("100")

    def action_approve(self):
        """Approve the budget (marks original as immutable)."""
        for record in self:
            if record.status != "draft":
                raise ValidationError("Only draft budgets can be approved.")
            record.status = "approved"

    def action_lock(self):
        """Lock the budget to prevent any further changes."""
        for record in self:
            if record.status != "approved":
                raise ValidationError("Only approved budgets can be locked.")
            record.status = "locked"


class RemontBudgetLine(models.Model):
    _name = "remont.budget.line"
    _description = "Budget Line Item"
    _order = "category, id"

    budget_id = fields.Many2one(
        "remont.budget",
        string="Budget",
        required=True,
        ondelete="cascade",
    )
    category = fields.Selection(
        selection=BUDGET_LINE_CATEGORIES,
        string="Category",
        required=True,
    )
    description = fields.Char(
        string="Description",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="budget_id.currency_id",
        store=True,
    )
    estimate_amount = fields.Monetary(
        string="Estimate",
        currency_field="currency_id",
    )
    actual_amount = fields.Monetary(
        string="Actual",
        currency_field="currency_id",
    )
    variance = fields.Monetary(
        string="Variance",
        currency_field="currency_id",
        compute="_compute_variance",
        store=True,
        help="Actual minus Estimate. Positive = over budget.",
    )

    @api.depends("estimate_amount", "actual_amount")
    def _compute_variance(self):
        for line in self:
            # Use Decimal for monetary arithmetic — NEVER float
            actual = Decimal(str(line.actual_amount or 0))
            estimate = Decimal(str(line.estimate_amount or 0))
            line.variance = float(actual - estimate)

    @api.constrains("estimate_amount", "actual_amount")
    def _check_amounts_positive(self):
        for line in self:
            if line.estimate_amount and line.estimate_amount < 0:
                raise ValidationError("Estimate amount must be non-negative.")
            if line.actual_amount and line.actual_amount < 0:
                raise ValidationError("Actual amount must be non-negative.")

    def write(self, vals):
        """Enforce immutability of estimate_amount on original approved budgets."""
        for line in self:
            budget = line.budget_id
            if budget.is_original and budget.status == "approved":
                if "estimate_amount" in vals:
                    raise ValidationError(
                        "Cannot modify estimate on an original approved budget. "
                        "Create a new budget version instead."
                    )
        return super().write(vals)
