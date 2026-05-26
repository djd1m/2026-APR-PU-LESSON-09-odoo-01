import uuid
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


TIMELAPSE_PERIODS = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
]

TIMELAPSE_STATUSES = [
    ("queued", "Queued"),
    ("processing", "Processing"),
    ("done", "Done"),
    ("failed", "Failed"),
]


class RemontTimelapseJob(models.Model):
    _name = "remont.timelapse.job"
    _description = "Timelapse Generation Job"
    _order = "create_date desc"

    project_id = fields.Many2one(
        "remont.project",
        string="Project",
        required=True,
        ondelete="cascade",
        index=True,
    )
    period = fields.Selection(
        selection=TIMELAPSE_PERIODS,
        string="Period",
        default="daily",
        required=True,
    )
    status = fields.Selection(
        selection=TIMELAPSE_STATUSES,
        string="Status",
        default="queued",
        required=True,
        tracking=True,
        index=True,
    )
    video_url = fields.Char(
        string="Video URL",
        help="URL of the generated timelapse video",
    )
    share_token = fields.Char(
        string="Share Token",
        default=lambda self: str(uuid.uuid4()),
        copy=False,
        index=True,
    )
    created_at = fields.Datetime(
        string="Created At",
        default=fields.Datetime.now,
        readonly=True,
    )
    completed_at = fields.Datetime(
        string="Completed At",
    )
    error_message = fields.Text(
        string="Error Message",
    )

    _sql_constraints = [
        (
            "share_token_unique",
            "UNIQUE(share_token)",
            "Share token must be unique.",
        ),
    ]

    @api.model
    def _cron_enqueue_daily_timelapse(self):
        """
        Cron job: enqueue timelapse generation for all active projects.

        Runs daily at 3 AM. Creates a timelapse job for each project
        that is currently in progress and has at least one snapshot.
        """
        active_projects = self.env["remont.project"].search([
            ("status", "=", "in_progress"),
        ])

        created_count = 0
        for project in active_projects:
            # Only generate if the project has snapshots
            if not project.snapshot_ids:
                continue

            # Avoid duplicating a job for today
            today_start = fields.Datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            existing = self.search([
                ("project_id", "=", project.id),
                ("period", "=", "daily"),
                ("created_at", ">=", today_start),
            ], limit=1)
            if existing:
                continue

            self.create({
                "project_id": project.id,
                "period": "daily",
                "status": "queued",
            })
            created_count += 1

        _logger.info(
            "Timelapse cron: enqueued %d jobs for %d active projects",
            created_count,
            len(active_projects),
        )
        return True
