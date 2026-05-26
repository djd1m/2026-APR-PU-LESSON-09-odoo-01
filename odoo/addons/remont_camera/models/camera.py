from odoo import models, fields, api
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

MAX_CAMERAS_PER_PROJECT = 4

CAMERA_STATUSES = [
    ("active", "Active"),
    ("inactive", "Inactive"),
    ("maintenance", "Maintenance"),
]


class RemontCamera(models.Model):
    _name = "remont.camera"
    _description = "Surveillance Camera"
    _order = "installed_at desc"
    _rec_name = "serial_number"

    serial_number = fields.Char(
        string="Serial Number",
        required=True,
        index=True,
    )
    rtsp_url = fields.Char(
        string="RTSP URL",
        required=True,
    )
    status = fields.Selection(
        selection=CAMERA_STATUSES,
        string="Status",
        default="active",
        required=True,
        tracking=True,
    )
    project_id = fields.Many2one(
        "remont.project",
        string="Project",
        required=True,
        ondelete="cascade",
        index=True,
    )
    installed_at = fields.Datetime(
        string="Installed At",
        default=fields.Datetime.now,
    )
    returned_at = fields.Datetime(
        string="Returned At",
    )
    capture_interval_minutes = fields.Integer(
        string="Capture Interval (minutes)",
        default=15,
        required=True,
        help="Interval between snapshot captures in minutes (5-60).",
    )
    last_capture_at = fields.Datetime(
        string="Last Capture At",
        help="Timestamp of the last successful snapshot capture.",
    )

    snapshot_ids = fields.One2many(
        "remont.snapshot",
        "camera_id",
        string="Snapshots",
    )
    snapshot_count = fields.Integer(
        string="Snapshot Count",
        compute="_compute_snapshot_count",
    )

    _sql_constraints = [
        (
            "serial_number_uniq",
            "UNIQUE(serial_number)",
            "Camera serial number must be unique.",
        ),
    ]

    @api.depends("snapshot_ids")
    def _compute_snapshot_count(self):
        for record in self:
            record.snapshot_count = len(record.snapshot_ids)

    @api.constrains("returned_at", "installed_at")
    def _check_returned_after_installed(self):
        for record in self:
            if (
                record.returned_at
                and record.installed_at
                and record.returned_at < record.installed_at
            ):
                raise ValidationError(
                    "Return date must be after installation date."
                )

    @api.constrains("capture_interval_minutes")
    def _check_capture_interval(self):
        for record in self:
            if record.capture_interval_minutes < 5 or record.capture_interval_minutes > 60:
                raise ValidationError(
                    "Capture interval must be between 5 and 60 minutes."
                )

    @api.constrains("project_id")
    def _check_max_cameras_per_project(self):
        for record in self:
            camera_count = self.search_count([
                ("project_id", "=", record.project_id.id),
            ])
            if camera_count > MAX_CAMERAS_PER_PROJECT:
                raise ValidationError(
                    "Maximum %d cameras per project." % MAX_CAMERAS_PER_PROJECT
                )
