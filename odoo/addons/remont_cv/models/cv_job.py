from odoo import models, fields


CV_JOB_STATUSES = [
    ("queued", "Queued"),
    ("processing", "Processing"),
    ("done", "Done"),
    ("failed", "Failed"),
]


class RemontCvJob(models.Model):
    _name = "remont.cv.job"
    _description = "Computer Vision Job"
    _order = "create_date desc"

    snapshot_id = fields.Many2one(
        "remont.snapshot",
        string="Snapshot",
        required=True,
        ondelete="cascade",
        index=True,
    )
    status = fields.Selection(
        selection=CV_JOB_STATUSES,
        string="Status",
        default="queued",
        required=True,
        tracking=True,
        index=True,
    )
    stage_result = fields.Char(
        string="Detected Stage",
        help="Renovation stage detected by the CV model",
    )
    confidence = fields.Float(
        string="Confidence",
        default=0.0,
        help="CV model confidence score (0.0 - 1.0)",
    )
    processed_at = fields.Datetime(
        string="Processed At",
    )
    error_message = fields.Text(
        string="Error Message",
        help="Error details if the job failed",
    )
