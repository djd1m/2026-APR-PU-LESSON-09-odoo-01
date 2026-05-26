from odoo import models, fields, api
from odoo.exceptions import ValidationError
from decimal import Decimal


RENOVATION_TYPES = [
    ("new", "New Construction"),
    ("renovation", "Renovation"),
]

PROJECT_STATUSES = [
    ("draft", "Draft"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
]


class RemontProject(models.Model):
    _name = "remont.project"
    _inherit = ["project.project"]
    _description = "Renovation Project"

    address = fields.Char(string="Address")
    area_sqm = fields.Float(string="Area (sq.m)")
    type = fields.Selection(
        selection=RENOVATION_TYPES,
        string="Renovation Type",
        default="renovation",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    budget_estimate = fields.Monetary(
        string="Budget Estimate",
        currency_field="currency_id",
    )
    budget_actual = fields.Monetary(
        string="Budget Actual",
        currency_field="currency_id",
    )

    start_date = fields.Date(string="Start Date")
    end_date_plan = fields.Date(string="Planned End Date")
    end_date_predict = fields.Date(string="Predicted End Date")

    status = fields.Selection(
        selection=PROJECT_STATUSES,
        string="Status",
        default="draft",
        tracking=True,
    )

    owner_id = fields.Many2one(
        "res.users",
        string="Owner",
        tracking=True,
    )
    contractor_id = fields.Many2one(
        "res.users",
        string="Contractor",
        tracking=True,
    )

    camera_ids = fields.One2many(
        "remont.camera",
        "project_id",
        string="Cameras",
    )
    stage_ids = fields.One2many(
        "remont.stage",
        "project_id",
        string="Stages",
    )
    snapshot_ids = fields.One2many(
        "remont.snapshot",
        "project_id",
        string="Snapshots",
    )
    timelapse_ids = fields.One2many(
        "remont.timelapse",
        "project_id",
        string="Timelapses",
    )
    alert_ids = fields.One2many(
        "remont.alert",
        "project_id",
        string="Alerts",
    )
    subscription_id = fields.Many2one(
        "remont.subscription",
        string="Subscription",
    )

    @api.constrains("budget_estimate", "budget_actual")
    def _check_budget_positive(self):
        for record in self:
            if record.budget_estimate and record.budget_estimate < 0:
                raise ValidationError("Budget estimate must be positive.")
            if record.budget_actual and record.budget_actual < 0:
                raise ValidationError("Budget actual must be positive.")

    @api.constrains("start_date", "end_date_plan")
    def _check_dates(self):
        for record in self:
            if (
                record.start_date
                and record.end_date_plan
                and record.start_date > record.end_date_plan
            ):
                raise ValidationError(
                    "Planned end date must be after start date."
                )
