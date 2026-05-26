import uuid

from odoo import fields, models


REMONT_ROLES = [
    ("viewer", "Viewer"),
    ("owner", "Owner"),
    ("contractor", "Contractor"),
    ("worker", "Worker"),
]


class ResUsers(models.Model):
    _inherit = "res.users"

    remont_role = fields.Selection(
        selection=REMONT_ROLES,
        string="RemontERP Role",
        default="viewer",
        readonly=True,
        help="Role in RemontERP system. Can only be changed by administrators.",
    )
    telegram_id = fields.Char(
        string="Telegram ID",
        help="Telegram user ID for bot integration.",
    )
    referral_code = fields.Char(
        string="Referral Code",
        default=lambda self: uuid.uuid4().hex[:8],
        readonly=True,
        copy=False,
        help="Unique referral code for user invitations.",
    )
