from odoo import models, fields, api


CV_JOB_STATUSES = [
    ("queued", "Queued"),
    ("processing", "Processing"),
    ("done", "Done"),
    ("failed", "Failed"),
]

STAGE_RESULTS = [
    ("demolition", "Demolition"),
    ("electrical", "Electrical"),
    ("plumbing", "Plumbing"),
    ("plaster", "Plaster"),
    ("screed", "Screed"),
    ("tiles", "Tiles"),
    ("painting", "Painting"),
    ("finishing", "Finishing"),
    ("unknown", "Unknown"),
]

DEFAULT_CONFIDENCE_THRESHOLD = 0.65


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
    stage_result = fields.Selection(
        selection=STAGE_RESULTS,
        string="Detected Stage",
        help="Renovation stage detected by the CV model",
        index=True,
    )
    confidence = fields.Float(
        string="Confidence",
        default=0.0,
        digits=(3, 4),
        help="CV model confidence score (0.0 - 1.0)",
    )
    model_version = fields.Char(
        string="Model Version",
        help="Version of the YOLOv8 model used for classification",
    )
    processed_at = fields.Datetime(
        string="Processed At",
    )
    needs_manual_review = fields.Boolean(
        string="Needs Manual Review",
        compute="_compute_needs_manual_review",
        store=True,
        help="True when confidence is below the configured threshold",
    )
    error_message = fields.Text(
        string="Error Message",
        help="Error details if the job failed",
    )

    @api.depends("confidence", "status")
    def _compute_needs_manual_review(self):
        ICP = self.env["ir.config_parameter"].sudo()
        threshold = float(
            ICP.get_param(
                "remont_cv.confidence_threshold",
                str(DEFAULT_CONFIDENCE_THRESHOLD),
            )
        )
        for record in self:
            if record.status == "done" and record.confidence < threshold:
                record.needs_manual_review = True
            else:
                record.needs_manual_review = False
