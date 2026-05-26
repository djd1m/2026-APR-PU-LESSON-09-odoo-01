import uuid
import logging
from datetime import timedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

REFERRAL_STATUSES = [
    ("pending", "Pending"),
    ("activated", "Activated"),
    ("expired", "Expired"),
]

# Maximum referral rewards a referrer can earn per calendar month
MAX_MONTHLY_REWARDS = 10


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
    activated_at = fields.Datetime(
        string="Activated At",
        readonly=True,
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
            record.write({
                "status": "activated",
                "activated_at": fields.Datetime.now(),
            })

    def _get_monthly_activation_count(self, referrer_id):
        """Count how many referral rewards were activated for a referrer
        in the current calendar month."""
        now = fields.Datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        count = self.search_count([
            ("referrer_id", "=", referrer_id),
            ("status", "=", "activated"),
            ("activated_at", ">=", month_start),
        ])
        return count

    def activate_referral_bonus(self, referred_user_id):
        """Called when a referred user subscribes to Pro.

        Activates the pending referral and extends the referrer's
        subscription by bonus_days, subject to the monthly cap.
        """
        referral = self.search([
            ("referred_id", "=", referred_user_id),
            ("status", "=", "pending"),
        ], limit=1)

        if not referral:
            _logger.info(
                "No pending referral found for user %s", referred_user_id
            )
            return False

        # Activate the referral record
        referral.action_activate()

        # Check monthly cap for the referrer
        monthly_count = self._get_monthly_activation_count(
            referral.referrer_id.id
        )
        if monthly_count > MAX_MONTHLY_REWARDS:
            _logger.warning(
                "Referrer %s hit monthly cap (%d/%d). "
                "Referral activated but no subscription extension.",
                referral.referrer_id.id,
                monthly_count,
                MAX_MONTHLY_REWARDS,
            )
            return True

        # Extend referrer's active subscription
        Subscription = self.env["remont.subscription"]
        referrer_sub = Subscription.search([
            ("user_id", "=", referral.referrer_id.id),
            ("tier", "in", ["pro", "enterprise"]),
        ], limit=1, order="end_date desc")

        if referrer_sub and referrer_sub.end_date:
            new_end = referrer_sub.end_date + timedelta(
                days=referral.bonus_days
            )
            referrer_sub.write({"end_date": new_end})
            _logger.info(
                "Extended subscription for referrer %s by %d days "
                "(new end_date: %s)",
                referral.referrer_id.id,
                referral.bonus_days,
                new_end,
            )
        else:
            _logger.warning(
                "Referrer %s has no active subscription to extend.",
                referral.referrer_id.id,
            )

        return True
