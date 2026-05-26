from odoo import models, fields, api
from odoo.exceptions import ValidationError


SUBSCRIPTION_PLANS = [
    ("basic", "Basic"),
    ("pro", "Professional"),
    ("business", "Business"),
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
        default="basic",
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
