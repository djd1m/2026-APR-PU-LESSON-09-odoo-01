from odoo import models, fields


PAYMENT_STATUSES = [
    ("pending", "Pending"),
    ("succeeded", "Succeeded"),
    ("failed", "Failed"),
    ("refunded", "Refunded"),
]


class RemontPayment(models.Model):
    _name = "remont.payment"
    _description = "Payment Record"
    _order = "create_date desc"

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

    status = fields.Selection(
        selection=PAYMENT_STATUSES,
        string="Status",
        required=True,
        default="pending",
        tracking=True,
    )

    yukassa_id = fields.Char(
        string="YuKassa Payment ID",
        index=True,
    )
    webhook_verified = fields.Boolean(
        string="Webhook Verified",
        default=False,
    )

    subscription_id = fields.Many2one(
        "remont.subscription",
        string="Subscription",
        ondelete="set null",
        index=True,
    )

    _sql_constraints = [
        (
            "yukassa_id_uniq",
            "UNIQUE(yukassa_id)",
            "YuKassa payment ID must be unique (idempotency).",
        ),
    ]
