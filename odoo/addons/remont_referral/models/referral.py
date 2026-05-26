import uuid

from odoo import models, fields, api
from odoo.exceptions import ValidationError


REFERRAL_STATUSES = [
    ("pending", "Pending"),
    ("activated", "Activated"),
    ("expired", "Expired"),
]


class RemontReferral(models.Model):
    _name = "remont.referral"
    _description = "Referral"
    _order = "create_date desc"

    referrer_id = fields.Many2one(
        "res.users",
        string="Referrer",
        required=True,
        ondelete="cascade",
        index=True,
    )
    referred_id = fields.Many2one(
        "res.users",
        string="Referred User",
        ondelete="set null",
        index=True,
    )
    share_token = fields.Char(
        string="Share Token",
        required=True,
        readonly=True,
        default=lambda self: str(uuid.uuid4()),
        copy=False,
        index=True,
    )
    bonus_days = fields.Integer(
        string="Bonus Days",
        default=7,
    )
    status = fields.Selection(
        selection=REFERRAL_STATUSES,
        string="Status",
        default="pending",
        tracking=True,
    )

    _sql_constraints = [
        (
            "share_token_unique",
            "UNIQUE(share_token)",
            "Share token must be unique.",
        ),
        (
            "referred_unique",
            "UNIQUE(referred_id)",
            "A user can only be referred once.",
        ),
    ]

    @api.constrains("referrer_id", "referred_id")
    def _check_no_self_referral(self):
        for record in self:
            if (
                record.referrer_id
                and record.referred_id
                and record.referrer_id == record.referred_id
            ):
                raise ValidationError("A user cannot refer themselves.")

    @api.constrains("bonus_days")
    def _check_bonus_days_positive(self):
        for record in self:
            if record.bonus_days < 0:
                raise ValidationError("Bonus days must be non-negative.")

    def action_activate(self):
        """Activate a pending referral and grant bonus days."""
        for record in self:
            if record.status != "pending":
                raise ValidationError(
                    "Only pending referrals can be activated."
                )
            record.status = "activated"
