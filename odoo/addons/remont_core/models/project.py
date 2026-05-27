from odoo import models, fields, api
from odoo.exceptions import ValidationError
from decimal import Decimal


RENOVATION_TYPES = [
    ("new", "New Construction"),
    ("renovation", "Renovation"),
]

PROJECT_STATUSES = [
    ("draft", "Draft"),
    ("planning", "Planning"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("on_hold", "On Hold"),
    ("cancelled", "Cancelled"),
]


class RemontProject(models.Model):
    _name = "remont.project"
    _description = "Renovation Project"
    _order = "create_date desc"

    name = fields.Char(string="Project Name", required=True)
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

    # One2many fields — defined here, comodels in their respective modules.
    # Odoo resolves these lazily when the dependent module is installed.
    stage_ids = fields.One2many(
        "remont.stage",
        "project_id",
        string="Stages",
    )

    overall_progress = fields.Float(
        string="Overall Progress (%)",
        compute="_compute_overall_progress",
        store=True,
    )

    @api.depends("stage_ids.progress_pct", "stage_ids.weight")
    def _compute_overall_progress(self):
        for record in self:
            stages = record.stage_ids
            if not stages:
                record.overall_progress = 0.0
                continue
            total_weight = sum(
                Decimal(str(s.weight or 1.0)) for s in stages
            )
            if total_weight == Decimal("0"):
                record.overall_progress = 0.0
                continue
            weighted_sum = sum(
                Decimal(str(s.progress_pct)) * Decimal(str(s.weight or 1.0))
                for s in stages
            )
            record.overall_progress = float(weighted_sum / total_weight)

    DEFAULT_STAGES = [
        ('demolition', 'Демонтаж', 1),
        ('electrical', 'Электрика', 2),
        ('plumbing', 'Сантехника', 3),
        ('plaster', 'Штукатурка', 4),
        ('screed', 'Стяжка', 5),
        ('tiles', 'Плитка', 6),
        ('painting', 'Покраска', 7),
        ('finishing', 'Чистовая отделка', 8),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """Create project and auto-generate 8 renovation stages."""
        projects = super().create(vals_list)
        for project in projects:
            if not project.stage_ids:
                for stage_name, stage_label, seq in self.DEFAULT_STAGES:
                    self.env['remont.stage'].create({
                        'name': stage_name,
                        'project_id': project.id,
                        'sequence': seq,
                        'status': 'planned',
                        'progress_pct': 0.0,
                    })
        return projects

    def action_start(self):
        """Move project from draft to in_progress."""
        for project in self:
            if project.status == 'draft':
                project.write({
                    'status': 'in_progress',
                    'start_date': fields.Date.today(),
                })

    def _check_auto_complete(self):
        """Auto-complete project when all stages are done."""
        for project in self:
            if project.status == 'in_progress' and project.stage_ids:
                if all(s.status == 'done' for s in project.stage_ids):
                    project.write({'status': 'completed'})

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
