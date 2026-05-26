from datetime import timedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError


SUBSCRIPTION_PLANS = [
    ("free", "Free"),
    ("pro", "Professional"),
    ("enterprise", "Enterprise"),
]

SUBSCRIPTION_STATUSES = [
    ("trial", "Trial"),
    ("active", "Active"),
    ("expired", "Expired"),
    ("cancelled", "Cancelled"),
]


class RemontSubscription(models.Model):
    _name = "remont.subscription"
    _description = "Subscription Plan"
    _order = "start_date desc"

    plan = fields.Selection(
        selection=SUBSCRIPTION_PLANS,
        string="Plan",
        required=True,
        default="free",
    )
    status = fields.Selection(
        selection=SUBSCRIPTION_STATUSES,
        string="Status",
        required=True,
        default="trial",
        tracking=True,
    )
    start_date = fields.Date(
        string="Start Date",
        required=True,
        default=fields.Date.today,
    )
    end_date = fields.Date(
        string="End Date",
        required=True,
    )
    auto_renew = fields.Boolean(
        string="Auto Renew",
        default=True,
        help="Automatically renew subscription via YuKassa saved payment method.",
    )
    grace_period_end = fields.Date(
        string="Grace Period End",
        compute="_compute_grace_period_end",
        store=True,
        help="3 days after end_date. User is downgraded to Free after this date.",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    amount = fields.Monetary(
        string="Amount",
        currency_field="currency_id",
        required=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        ondelete="cascade",
        index=True,
    )

    payment_ids = fields.One2many(
        "remont.payment",
        "subscription_id",
        string="Payments",
    )

    @api.depends("end_date")
    def _compute_grace_period_end(self):
        for record in self:
            if record.end_date:
                record.grace_period_end = record.end_date + timedelta(days=3)
            else:
                record.grace_period_end = False

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for record in self:
            if (
                record.start_date
                and record.end_date
                and record.start_date > record.end_date
            ):
                raise ValidationError(
                    "End date must be after start date."
                )

    @api.constrains("amount")
    def _check_amount_positive(self):
        for record in self:
            if record.amount < 0:
                raise ValidationError(
                    "Subscription amount must be non-negative."
                )
