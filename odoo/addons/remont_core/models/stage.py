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
