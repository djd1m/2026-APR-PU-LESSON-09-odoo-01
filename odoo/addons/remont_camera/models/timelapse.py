from odoo import models, fields, api
from odoo.exceptions import ValidationError


TIMELAPSE_PERIODS = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
]


class RemontTimelapse(models.Model):
    _name = "remont.timelapse"
    _description = "Timelapse Video"
    _order = "date_from desc"

    video_url = fields.Char(
        string="Video URL",
        required=True,
    )
    duration_sec = fields.Integer(
        string="Duration (seconds)",
        default=0,
    )
    period = fields.Selection(
        selection=TIMELAPSE_PERIODS,
        string="Period",
        required=True,
    )
    date_from = fields.Date(
        string="Date From",
        required=True,
    )
    date_to = fields.Date(
        string="Date To",
        required=True,
    )
    project_id = fields.Many2one(
        "remont.project",
        string="Project",
        required=True,
        ondelete="cascade",
        index=True,
    )
    camera_id = fields.Many2one(
        "remont.camera",
        string="Camera",
        ondelete="set null",
        index=True,
        help="Source camera for this timelapse video.",
    )
    share_token = fields.Char(
        string="Share Token",
        index=True,
    )
    frame_count = fields.Integer(
        string="Frame Count",
        default=0,
        help="Number of snapshot frames used to generate this timelapse.",
    )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to and record.date_from > record.date_to:
                raise ValidationError(
                    "Date To must be after Date From."
                )

    @api.constrains("duration_sec")
    def _check_duration(self):
        for record in self:
            if record.duration_sec < 0:
                raise ValidationError(
                    "Duration must be non-negative."
                )

    @api.constrains("frame_count")
    def _check_frame_count(self):
        for record in self:
            if record.frame_count < 0:
                raise ValidationError(
                    "Frame count must be non-negative."
                )
