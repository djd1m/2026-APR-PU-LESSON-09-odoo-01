from odoo import models, fields, api
from odoo.exceptions import ValidationError


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

    snapshot_ids = fields.One2many(
        "remont.snapshot",
        "camera_id",
        string="Snapshots",
    )

    _sql_constraints = [
        (
            "serial_number_uniq",
            "UNIQUE(serial_number)",
            "Camera serial number must be unique.",
        ),
    ]

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
