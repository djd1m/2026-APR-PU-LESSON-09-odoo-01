from odoo import models, fields


ALERT_TYPES = [
    ("absence", "Crew Absence"),
    ("overbudget", "Budget Overrun"),
    ("delay", "Schedule Delay"),
    ("camera_error", "Camera Error"),
]

ALERT_SEVERITIES = [
    ("info", "Info"),
    ("warning", "Warning"),
    ("critical", "Critical"),
]


class RemontAlert(models.Model):
    _name = "remont.alert"
    _description = "Project Alert"
    _order = "created_at desc"

    type = fields.Selection(
        selection=ALERT_TYPES,
        string="Type",
        required=True,
    )
    severity = fields.Selection(
        selection=ALERT_SEVERITIES,
        string="Severity",
        required=True,
        default="warning",
    )
    message = fields.Text(
        string="Message",
        required=True,
    )
    is_read = fields.Boolean(
        string="Read",
        default=False,
    )
    project_id = fields.Many2one(
        "remont.project",
        string="Project",
        required=True,
        ondelete="cascade",
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="User",
        ondelete="set null",
        index=True,
    )
    created_at = fields.Datetime(
        string="Created At",
        default=fields.Datetime.now,
        readonly=True,
    )
