from odoo import models, fields, api
from odoo.exceptions import ValidationError


STAGE_NAMES = [
    ("demolition", "Demolition"),
    ("electrical", "Electrical"),
    ("plumbing", "Plumbing"),
    ("plaster", "Plaster"),
    ("screed", "Screed"),
    ("tiles", "Tiles"),
    ("painting", "Painting"),
    ("finishing", "Finishing"),
]

STAGE_STATUSES = [
    ("planned", "Planned"),
    ("in_progress", "In Progress"),
    ("done", "Done"),
]


class RemontStage(models.Model):
    _name = "remont.stage"
    _description = "Renovation Stage"
    _order = "sequence, id"

    name = fields.Selection(
        selection=STAGE_NAMES,
        string="Stage",
        required=True,
    )
    progress_pct = fields.Float(
        string="Progress (%)",
        default=0.0,
    )
    status = fields.Selection(
        selection=STAGE_STATUSES,
        string="Status",
        default="planned",
    )
    weight = fields.Float(
        string="Weight",
        default=1.0,
        help="Weight for overall project progress calculation.",
    )

    planned_start = fields.Date(string="Planned Start")
    planned_end = fields.Date(string="Planned End")
    actual_start = fields.Date(string="Actual Start")
    actual_end = fields.Date(string="Actual End")

    project_id = fields.Many2one(
        "remont.project",
        string="Project",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )
    dependency_ids = fields.Many2many(
        "remont.stage",
        "remont_stage_dependency_rel",
        "stage_id",
        "dependency_id",
        string="Dependencies",
        help="Predecessor stages that must be completed before this stage can start.",
    )
    checklist_ids = fields.One2many(
        "remont.checklist.item",
        "stage_id",
        string="Checklist Items",
    )
    checklist_progress = fields.Float(
        string="Checklist Progress (%)",
        compute="_compute_checklist_progress",
        store=True,
    )

    @api.depends("checklist_ids.is_done")
    def _compute_checklist_progress(self):
        for record in self:
            items = record.checklist_ids
            if not items:
                record.checklist_progress = 0.0
                continue
            done_count = len(items.filtered(lambda i: i.is_done))
            record.checklist_progress = (done_count / len(items)) * 100.0

    @api.constrains("progress_pct")
    def _check_progress(self):
        for record in self:
            if record.progress_pct < 0 or record.progress_pct > 100:
                raise ValidationError(
                    "Progress must be between 0 and 100."
                )

    @api.constrains("planned_start", "planned_end")
    def _check_planned_dates(self):
        for record in self:
            if (
                record.planned_start
                and record.planned_end
                and record.planned_start > record.planned_end
            ):
                raise ValidationError(
                    "Planned end date must be after planned start date."
                )

    @api.constrains("status")
    def _check_dependencies_before_start(self):
        """Prevent starting a stage if predecessor stages are not done."""
        for record in self:
            if record.status == "in_progress" and record.dependency_ids:
                not_done = record.dependency_ids.filtered(
                    lambda d: d.status != "done"
                )
                if not_done:
                    names = ", ".join(
                        dict(STAGE_NAMES).get(d.name, d.name)
                        for d in not_done
                    )
                    raise ValidationError(
                        f"Cannot start this stage. "
                        f"Predecessor stages not completed: {names}"
                    )

    @api.constrains("status", "checklist_ids")
    def _check_checklist_before_done(self):
        """Prevent marking stage done if checklist items are incomplete."""
        for record in self:
            if record.status == "done" and record.checklist_ids:
                unchecked = record.checklist_ids.filtered(
                    lambda i: not i.is_done
                )
                if unchecked:
                    raise ValidationError(
                        "Complete all checklist items first."
                    )
